import os
import cv2
from retinaface import RetinaFace
from keras_facenet import FaceNet
import numpy as np
import json
import re
import shutil

class FaceDetectionService:
    def __init__(self, folder_index):
        self.frames_dir = f"extracted_frames_{folder_index}"
        self.output_file = f"people_tracking_output_{folder_index}.txt"
        self.json_output_file = f"formatted_output_{folder_index}.json"

    def extract_audio_frames(self, video_path, frame_interval_seconds=4):
        print("Inside extract audio frames")
        os.makedirs(self.frames_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * frame_interval_seconds)
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                frame_path = os.path.join(self.frames_dir, f"frame_{frame_count:06d}.jpg")
                success = cv2.imwrite(frame_path, frame)
                if not success:
                    print(f"Warning: Failed to save frame {frame_path}")
            frame_count += 1
        cap.release()
        print(f"Frames extracted every {frame_interval_seconds} seconds.")

    def count_and_track_people(self, fps=30, distance_threshold=0.9):
        print("Inside count and track people")
        embedder = FaceNet()
        unknown_mapping = {}
        unknown_counter = 1
        output = []

        for frame_file in sorted(os.listdir(self.frames_dir)):
            frame_path = os.path.join(self.frames_dir, frame_file)
            frame = cv2.imread(frame_path)
            if frame is None:
                print(f"Warning: Frame {frame_file} could not be read. Skipping...")
                continue

            faces = RetinaFace.extract_faces(frame, align=True)
            timestamp = int(frame_file.split("_")[1].split(".")[0]) / fps

            if not faces:
                output.append({"timestamp": timestamp, "faces": []})
                continue

            detected_faces = []
            for face in faces:
                face_embedding = embedder.embeddings([face])[0]

                min_distance = float("inf")
                best_match = None
                for unk_label, unk_embedding in unknown_mapping.items():
                    if face_embedding.shape != unk_embedding.shape:
                        continue

                    distance = np.linalg.norm(face_embedding - unk_embedding)
                    if distance < min_distance:
                        min_distance = distance
                        best_match = unk_label

                if min_distance < distance_threshold:
                    detected_faces.append(best_match)
                else:
                    unknown_label = f"unknown-{unknown_counter}"
                    unknown_mapping[unknown_label] = face_embedding
                    detected_faces.append(unknown_label)
                    unknown_counter += 1
            output.append({"timestamp": timestamp, "faces": detected_faces})

        with open(self.output_file, "w") as f:
            for entry in output:
                f.write(str(entry) + "\n")

        print(f"People tracking results saved to {self.output_file}.")

    def format_output(self):
        print("Inside format output")
        with open(self.output_file, "r") as f:
            lines = f.readlines()

        total_faces_detected = set()
        not_in_frame_intervals = []
        last_no_face_time = None
        total_time_not_in_frame = 0
        multiple_faces_detected = False
        no_face_detected = False

        for line in lines:
            match = re.match(r"{\'timestamp\': (\d+\.\d+), \'faces\': \[(.*)\]}", line.strip())
            if match:
                timestamp = float(match.group(1))
                faces = match.group(2).replace("'", "").split(", ") if match.group(2) else []

                if not faces:
                    no_face_detected = True
                    if last_no_face_time is None:
                        last_no_face_time = timestamp
                else:
                    total_faces_detected.update(faces)
                    if len(faces) > 1:
                        multiple_faces_detected = True
                    if last_no_face_time is not None:
                        interval_duration = timestamp - last_no_face_time
                        total_time_not_in_frame += interval_duration
                        not_in_frame_intervals.append((last_no_face_time, timestamp))
                        last_no_face_time = None

        if last_no_face_time is not None:
            total_time_not_in_frame += timestamp - last_no_face_time
            not_in_frame_intervals.append((last_no_face_time, timestamp))

        formatted_output = {
            "numberOfFacesDetected": len(total_faces_detected),
            "multipleFacesDetected": multiple_faces_detected,
            "noFaceDetected": no_face_detected,
            "timePersonWasNotInFrame": f"{total_time_not_in_frame:.0f} seconds",
            "personNotInFrameDetails": {
                "timeNotInFrame": [
                    {
                        "start": f"{int(start // 60)}:{int(start % 60):02d}",
                        "end": f"{int(end // 60)}:{int(end % 60):02d}"
                    } for start, end in not_in_frame_intervals
                ]
            }
        }
        return formatted_output

    def calculate_proctoring_score(self, api_data):
        score = 100
        exit_fullscreen = api_data['exit_full_screen']
        tab_switch_count = api_data['tab_switch_count']
        tab_switch_time = api_data['tab_switch_time']
        multiple_faces = api_data['result']['multipleFacesDetected']
        time_not_in_frame_str = api_data['result']['timePersonWasNotInFrame']
        time_not_in_frame = int(time_not_in_frame_str.split()[0])

        P1 = 25 if exit_fullscreen else 0
        P2 = 12.5 if tab_switch_count > 5 else (8 if tab_switch_count > 2 else (4 if tab_switch_count > 0 else 0))
        P3 = 25 if multiple_faces else 0
        P4 = 12.5 if time_not_in_frame > 60 else (8 if time_not_in_frame > 30 else (4 if time_not_in_frame > 5 else 0))
        P5 = 25 if tab_switch_time > 60 else (15 if tab_switch_time > 30 else (10 if tab_switch_time > 5 else 0))

        total_penalty = P1 + P2 + P3 + P4 + P5
        final_score = max(score - total_penalty, 0)

        interpretation = (
            "Excellent (High Integrity)" if final_score >= 90 else
            "Good (Acceptable Integrity)" if final_score >= 75 else
            "Moderate (Potential Integrity Issues)" if final_score >= 50 else
            "Poor (Likely Integrity Violation)"
        )

        return {
            "Proctoring Final Score": final_score,
            "Proctoring Interpretation": interpretation
        }

    def processing_tab_timestamps(self, tab_switch_time, tab_switch_timestamps):
        if tab_switch_time > 0:
            return tab_switch_time
        print("tab_switch_time", tab_switch_time)

        if not isinstance(tab_switch_timestamps, list) or len(tab_switch_timestamps) % 2 != 0:
            print("length of tab_switch_timestamps:: ", len(tab_switch_timestamps))
            raise ValueError("Tab switch timestamps must be a list of paired timestamps.")

        def convert_time_to_seconds(timestamp):
            h, m, s = map(int, timestamp.split(":"))
            return h * 3600 + m * 60 + s

        total_time = 0
        for i in range(0, len(tab_switch_timestamps), 2):
            start_time = convert_time_to_seconds(tab_switch_timestamps[i])
            end_time = convert_time_to_seconds(tab_switch_timestamps[i + 1])
            total_time += end_time - start_time

        print("total time not in tab:: ", total_time)

        return total_time

    def process_video(self, video_path, candidate_id, tab_switch_count, tab_switch_timestamps, tab_switch_time, exit_full_screen):
        self.extract_audio_frames(video_path)
        self.count_and_track_people()
        formatted_output = self.format_output()
        formatted_output["tab_switch_count"] = tab_switch_count
        formatted_output["exit_full_screen"] = exit_full_screen
        candidate_id = candidate_id

        # Calculate tab switch time
        total_tab_switch_time = self.processing_tab_timestamps(tab_switch_time, tab_switch_timestamps)
        formatted_output["tab_switch_time"] = total_tab_switch_time

        proctor_score = self.calculate_proctoring_score({
            "exit_full_screen": exit_full_screen,
            "tab_switch_count": tab_switch_count,
            "tab_switch_time": total_tab_switch_time,
            "result": formatted_output
        })
        formatted_output["proctor_score"] = proctor_score
        self.cleanup()
        return formatted_output

    def cleanup(self):
        if os.path.exists(self.frames_dir):
            shutil.rmtree(self.frames_dir)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        print(f"Temporary files cleaned up for folder: {self.frames_dir}")