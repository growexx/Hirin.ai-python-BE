import os
import pandas as pd
import re
import logging
from openai import OpenAI
import google.generativeai as genai
from groq import Groq
import configparser
import json


# Load the config.ini file
# try:
#     config = configparser.ConfigParser()
#     config.read("config.ini")
#     API_KEYS = {
#         "OPENAI_API_KEY": config["API_KEYS"]["OPENAI_API_KEY"],
#         "GROQ_API_KEY": config["API_KEYS"]["GROQ_API_KEY"],
#         "GENAI_API_KEY": config["API_KEYS"]["GENAI_API_KEY"],
#     }
# except Exception as e:
#     logging.error(f"Failed to load API keys: {e}")
#     raise

# # Initialize API clients
# try:
#     openai_client = OpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
#     groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
#     genai.configure(api_key=API_KEYS["GENAI_API_KEY"])
# except Exception as e:
#     logging.error(f"Failed to initialize API clients: {e}")
#     raise

def read_prompt(file_name):
    try:
        with open(file_name, 'r') as file:
            content = file.read()
            logging.info(f"Successfully read prompt file: {file_name}")
            return content
    except Exception as e:
        logging.error(f"Failed to read prompt file {file_name}: {e}")
        return ""

def summarize_job_description_groq(groq_client, job_description, model):
    try:
        prompt_template = read_prompt("app/services/jd_summarization.txt")
        prompt_summarizing_JD = prompt_template.format(job_description=job_description)

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert at summarization task."},
                {"role": "user", "content": prompt_summarizing_JD},
            ],
            model=model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Failed to summarize job description with GROQ: {e}")
        return "Error in summarization"

def summarize_job_description_openai(openai_client, job_description):
    try:
        prompt_template = read_prompt("app/services/jd_summarization.txt")
        prompt_summarizing_JD = prompt_template.format(job_description=job_description)

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_summarizing_JD},
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Failed to summarize job description with OpenAI: {e}")
        return "Error in summarization"

def summarize_job_description_genai(genai, job_description):
    try:
        prompt_template = read_prompt("app/services/jd_summarization.txt")
        prompt_summarizing_JD = prompt_template.format(job_description=job_description)

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        gmodel = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
        )
        response = gmodel.generate_content(prompt_summarizing_JD)
        return response.text
    except Exception as e:
        logging.error(f"Failed to summarize job description with GenAI: {e}")
        return "Error in summarization"

def generate_questions(prompt, model, client):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            model=model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Failed to generate questions: {e}")
        return "Error generating questions"

def extract_and_save_questions(questions_output, output_excel_file, source):
    try:
        role, seniority_level = "", ""
        if isinstance(questions_output, str):
            role_match = re.search(r"Role:\s*(.+)", questions_output)
            seniority_level_match = re.search(r"Seniority Level:\s*(.+)", questions_output)
            role = role_match.group(1).strip() if role_match else "Unknown"
            seniority_level = seniority_level_match.group(1).strip() if seniority_level_match else "Unknown"

            parsed_questions = []
            current_question = {}
            buffer = ""

            for line in questions_output.splitlines():
                line = line.strip()

                if re.match(r"\*\*(Question\s+(Number\s*)?\d+:)\*\*", line) or re.match(r"Question\s+(Number\s*)?\d+:", line):
                    if current_question:
                        current_question["Question"] = buffer.strip()
                        parsed_questions.append(current_question)
                    current_question = {}
                    buffer = re.sub(r"^\*\*(Question\s+(Number\s*)?\d+:)\*\*|\bQuestion\s+(Number\s*)?\d+:\s*", "", line).strip(" *")
                elif line.startswith("**Estimated Time:**") or line.startswith("Estimated Time:"):
                    current_question["Estimated Time"] = re.sub(r"^.*Estimated Time:\s*", "", line).strip(" *")
                elif line.startswith("**Level of Difficulty:**") or line.startswith("Level of Difficulty:"):
                    current_question["Level of Difficulty"] = re.sub(r"^.*Level of Difficulty:\s*", "", line).strip(" *")
                elif line.startswith("**Topic:**") or line.startswith("Topic:"):
                    current_question["Topic"] = re.sub(r"^.*Topic:\s*", "", line).strip(" *")
                elif line.startswith("**Domain:**") or line.startswith("Domain:"):
                    current_question["Domain"] = re.sub(r"^.*Domain:\s*", "", line).strip(" *")
                elif line.startswith("**Skill Type:**") or line.startswith("Skill Type:"):
                    current_question["Skill Type"] = re.sub(r"^.*Skill Type:\s*", "", line).strip(" *")
                elif re.search(r"^\**\s*Question[-\s]?Type[:\s]", line, re.IGNORECASE):
                    current_question["Question-Type"] = re.sub(r"^\**\s*Question[-\s]?Type[:\s]*", "", line, flags=re.IGNORECASE).strip()
                else:
                    buffer += " " + line

            if current_question:
                current_question["Question"] = buffer.strip()
                parsed_questions.append(current_question)

        df = pd.DataFrame(parsed_questions, columns=["Question", "Estimated Time", "Level of Difficulty", "Topic", "Domain", "Skill Type", "Question-Type"])
        df["Role"] = role
        df["Seniority Level"] = seniority_level
        df["Source"] = source

        column_order = ["Question", "Estimated Time", "Level of Difficulty", "Topic", "Domain", "Skill Type", "Question-Type", "Role", "Seniority Level", "Source"]
        df = df[column_order]

        if os.path.exists(output_excel_file):
            existing_df = pd.read_excel(output_excel_file)
            final_df = pd.concat([existing_df, df], ignore_index=True)
            final_df.to_excel(output_excel_file, index=False)
        else:
            df.to_excel(output_excel_file, index=False)

        logging.info(f"Successfully saved questions to {output_excel_file}")
    except Exception as e:
        logging.error(f"Failed to extract and save questions: {e}")

def clean_asterisks(value):
    """Remove leading or trailing asterisks from a string."""
    if isinstance(value, str):
        return re.sub(r'^\*+|\*+$', '', value)
    return value

def json_questions():
    try:
        # List of Excel file paths
        file_paths = ['app/services/Questions_Llama.xlsx', 'app/services/Questions_GPT4.xlsx', 'app/services/Questions_Gemma.xlsx']  # Replace with actual file paths

        # Initialize the final JSON structure
        questions_json = {"questions": {}}

        # Process each file
        for file_path in file_paths:
            try:
                # Load the Excel file
                sheet_data = pd.read_excel(file_path, sheet_name='Sheet1')
                logging.info(f"Successfully loaded Excel file: {file_path}")

                # Group questions by the 'Source' column
                grouped_data = sheet_data.groupby('Source')

                # Transform data into the desired JSON format
                for source, group in grouped_data:
                    try:
                        # Ensure each source gets its unique key in the JSON
                        if source not in questions_json["questions"]:
                            questions_json["questions"][source] = []

                        # Append questions from this group
                        questions_json["questions"][source].extend(
                            group.apply(
                                lambda row: {
                                    "questionText": clean_asterisks(row["Question"]),
                                    "estimatedTime": clean_asterisks(row["Estimated Time"]),
                                    "difficultyLevel": clean_asterisks(row["Level of Difficulty"]),
                                    "topic": clean_asterisks(row["Topic"]),
                                    "domain": clean_asterisks(row["Domain"]),
                                    "skillType": clean_asterisks(row["Skill Type"]),
                                    "questionType": clean_asterisks(row["Question-Type"]),
                                    "role": clean_asterisks(row["Role"]),
                                    "seniorityLevel": clean_asterisks(row["Seniority Level"]),
                                },
                                axis=1,
                            ).tolist()
                        )
                        logging.info(f"Processed source: {source} from file: {file_path}")
                    except Exception as e:
                        logging.error(f"Error processing source {source} in file {file_path}: {e}")
            except FileNotFoundError:
                logging.error(f"File not found: {file_path}")
            except Exception as e:
                logging.error(f"Error loading Excel file {file_path}: {e}")
        return questions_json
    except Exception as e:
        logging.error(f"Failed to generate JSON structure: {e}")
        return {"questions": {}}

def delete_xlsx_files(folder_path):
    try:
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.xlsx'):
                os.remove(os.path.join(folder_path, file_name))
        print("All .xlsx files deleted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def process_job_description(openai_client, groq_client, job_description, noq):
    # Configure logging
    logging.basicConfig(
        filename='application.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        delete_xlsx_files("app/services")
    except Exception as e:
        logging.error(f"Deleting previously generated Excel Files: {e}")

    jd = job_description
    try:
        summaries = {
            "Llama": summarize_job_description_groq(groq_client, jd, "llama-3.3-70b-versatile"),
            "GPT4": summarize_job_description_openai(openai_client, jd),
            "Gemma": summarize_job_description_groq(groq_client, jd, "gemma2-9b-it"),
        }

        questions = {}
        for source, summarized_jd in summaries.items():
            try:
                if source == "Llama":
                    prompt_template = read_prompt("app/services/llama_prompt.txt")
                    prompt = prompt_template.format(summarized_jd=summarized_jd,no_of_questions=noq)
                    questions[source] = generate_questions(prompt, "llama-3.3-70b-versatile", groq_client)
                    logging.info(f"{source}, {questions[source]}")
                    extract_and_save_questions(questions[source], f"app/services/Questions_{source}.xlsx", source)
                elif source == "GPT4":
                    prompt_template = read_prompt("app/services/gpt4_prompt.txt")
                    prompt = prompt_template.format(summarized_jd=summarized_jd,no_of_questions=noq)
                    questions[source] = generate_questions(prompt, "gpt-4", openai_client)
                    extract_and_save_questions(questions[source], f"app/services/Questions_{source}.xlsx", source)
                    logging.info(f"{source}, {questions[source]}")
                elif source == "Gemma":
                    prompt_template = read_prompt("app/services/gemma_prompt.txt")
                    prompt = prompt_template.format(summarized_jd=summarized_jd,no_of_questions=noq)
                    questions[source] = generate_questions(prompt, "gemma2-9b-it", groq_client)
                    logging.info(f"{source}, {questions[source]}")
                    extract_and_save_questions(questions[source], f"app/services/Questions_{source}.xlsx", source)

                try:
                    questions = json_questions()
                    logging.info(f"JSONIFY,{questions}")
                except Exception as e:
                    logging.error(f"Error formatting the questions in Json {source}: {e}")
            except Exception as e:
                logging.error(f"Error generating questions for {source}: {e}")
                questions[source] = f"Error generating questions: {e}"

        return questions
    except Exception as e:
        logging.error(f"Failed to process job description: {e}")
        return {}
