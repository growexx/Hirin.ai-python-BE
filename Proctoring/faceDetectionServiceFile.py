import os
import cv2
from retinaface import RetinaFace
from keras_facenet import FaceNet
import numpy as np
import re
import shutil
from logger.logger_config import logger

class FaceDetectionService:
    def __init__(self, folder_index):
        self.frames_dir = f"extracted_frames_{folder_index}"
        self.output_file = f"people_tracking_output_{folder_index}.txt"

    def extract_audio_frames(self, video_path, frame_interval_seconds=4):
        try:
            logger.info("Extracting frames from video.")
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
                    cv2.imwrite(frame_path, frame)
                frame_count += 1

            cap.release()
            logger.info(f"Frames extracted and saved to {self.frames_dir}.")
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            raise

    def count_and_track_people(self, fps=30, distance_threshold=0.9, max_retries=3):
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"Starting people detection and tracking. Retry attempt: {retry_count + 1}")
                embedder = FaceNet()
                unknown_mapping = {}
                unknown_counter = 1
                output = []

                invalid_frames = []

                for frame_file in sorted(os.listdir(self.frames_dir)):
                    frame_path = os.path.join(self.frames_dir, frame_file)
                    frame = cv2.imread(frame_path)

                    if frame is None or frame.size == 0:
                        logger.warning(f"Invalid or empty frame: {frame_path}. Marking for removal.")
                        invalid_frames.append(frame_file)
                        continue

                    faces = RetinaFace.extract_faces(frame, align=True)
                    if not faces:
                        logger.warning(f"No faces detected in frame {frame_file}. Marking for removal.")
                        invalid_frames.append(frame_file)
                        continue

                    timestamp = int(frame_file.split("_")[1].split(".")[0]) / fps

                    detected_faces = []
                    for face in faces:
                        if face is None or face.size == 0:
                            logger.warning("Invalid face detected, skipping...")
                            continue

                        try:
                            face_embedding = embedder.embeddings([face])[0]
                        except Exception as e:
                            logger.error(f"Error generating embeddings for a face: {e}. Skipping...")
                            continue

                        min_distance = float("inf")
                        best_match = None

                        for unk_label, unk_embedding in unknown_mapping.items():
                            if face_embedding.shape == unk_embedding.shape:
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

                logger.info(f"People tracking results saved to {self.output_file}.")
                
                # Break out of the retry loop on success
                break

            except Exception as e:
                logger.error(f"Error in people detection and tracking: {e}. Retrying...")
                retry_count += 1

                # Remove invalid frames before retrying
                for invalid_frame in invalid_frames:
                    invalid_frame_path = os.path.join(self.frames_dir, invalid_frame)
                    if os.path.exists(invalid_frame_path):
                        os.remove(invalid_frame_path)
                        logger.info(f"Removed invalid frame: {invalid_frame_path}")

                invalid_frames.clear()  # Reset for the next retry

                if retry_count == max_retries:
                    logger.critical(f"Max retries reached. Aborting...")
                    raise

    def format_output(self):
        try:
            logger.info("Formatting detection output.")
            with open(self.output_file, "r") as f:
                lines = f.readlines()

            total_faces_detected = set()
            not_in_frame_intervals = []
            last_no_face_time = None
            total_time_not_in_frame = 0

            for line in lines:
                match = re.match(r"{'timestamp': (\d+\.\d+), 'faces': \[(.*)\]}", line.strip())
                if match:
                    timestamp = float(match.group(1))
                    faces = match.group(2).replace("'", "").split(", ") if match.group(2) else []

                    if not faces:
                        if last_no_face_time is None:
                            last_no_face_time = timestamp
                    else:
                        total_faces_detected.update(faces)
                        if last_no_face_time is not None:
                            total_time_not_in_frame += timestamp - last_no_face_time
                            not_in_frame_intervals.append((last_no_face_time, timestamp))
                            last_no_face_time = None

            formatted_output = {
                "numberOfFacesDetected": len(total_faces_detected),
                "multipleFacesDetected": len(total_faces_detected) > 1,
                "noFaceDetected": len(total_faces_detected) == 0,
                "timePersonWasNotInFrame": int(total_time_not_in_frame),
                "personNotInFrameDetails": {
                    "timeNotInFrame": [
                        {"start": f"{int(start // 60)}:{int(start % 60):02d}", "end": f"{int(end // 60)}:{int(end % 60):02d}"}
                        for start, end in not_in_frame_intervals
                    ]
                }
            }
            logger.info("Output formatting completed.")
            return formatted_output
        except Exception as e:
            logger.error(f"Error formatting output: {e}")
            raise

    def calculate_proctoring_score(self, api_data):
        score = 100
        exit_fullscreen = api_data['exit_full_screen']
        tab_switch_count = api_data['tab_switch_count']
        tab_switch_time = api_data['tab_switch_time']
        time_not_in_frame_str = api_data['result']['timePersonWasNotInFrame']
        time_not_in_frame = api_data['result']['timePersonWasNotInFrame']
        multiple_faces = api_data.get('multipleFacesDetected', False)

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

        if not isinstance(tab_switch_timestamps, list) or len(tab_switch_timestamps) % 2 != 0:
            raise ValueError("Tab switch timestamps must be a list of paired timestamps.")

        def convert_time_to_seconds(timestamp):
            h, m, s = map(int, timestamp.split(":"))
            return h * 3600 + m * 60 + s

        total_time = 0
        for i in range(0, len(tab_switch_timestamps), 2):
            start_time = convert_time_to_seconds(tab_switch_timestamps[i])
            end_time = convert_time_to_seconds(tab_switch_timestamps[i + 1])
            total_time += end_time - start_time

        return total_time

    def process_video(self, video_path, metadata):
        try:
            logger.info(f"Starting video processing for metadata: {metadata}")
            self.extract_audio_frames(video_path)
            self.count_and_track_people()  # Updated method with retries
            formatted_output = self.format_output()
            logger.info(f"Processing completed for video: {video_path}")
            return formatted_output
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        try:
            if os.path.exists(self.frames_dir):
                shutil.rmtree(self.frames_dir)
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
            logger.info(f"Temporary files cleaned up for {self.frames_dir}.")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")