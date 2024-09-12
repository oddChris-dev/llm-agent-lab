import gc
import textwrap
from datetime import datetime
import threading

import torch
import transformers

from utils.date_tools import DateTools


class TextGenerator:
    def __init__(self,
                 model_path: str = "models/Meta-Llama-3.1-8B-Instruct",
                 max_tokens: int = 256,
                 cuda_lock: threading.Lock = threading.Lock()):
        """
        Initializes the ChatbotModel with a path to the local LLM model.
        Args:
            model_path (str): The file path to the pretrained local LLM model (can be GGUF or transformer-supported).
            max_tokens (int): The maximum number of tokens that the input to the model can have.
        """
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.pipeline = None
        self.cuda_lock = cuda_lock
        self.log_path = "prompt-log.txt"
        self.enable_logging = False
        self.model_loaded = False
        self.ready_gate = threading.Event()

    def log(self, entry):
        if self.enable_logging:
            try:
                entry = str(entry).encode('ascii', errors='ignore').decode('ascii')
                with open(self.log_path, "a+") as f:
                    f.write(f"{textwrap.fill(entry, width=80)}\n")
            except Exception as ex:
                print(f"log exception {ex} for {entry}")

    def generate_response(self, prompt: str = "", input: str = "", history: list = None) -> str:
        self.wait_for_ready()

        current = datetime.now()
        date = DateTools.human_readable_date(current)
        time = DateTools.human_readable_time(current)

        input_records = [{
            "role": "system",
            "content": prompt.replace('DATE', date).replace('TIME', time)
        }]

        if history and isinstance(history, list) and len(history) > 0:
            input_records += history

        if input:
            clean_input = input.encode('ascii', errors='ignore').decode('ascii')
            next_prompt = {"role": "user", "content": clean_input}
            input_records.append(next_prompt)

        self.log("INPUT\n======\n")
        self.log(input_records)
        gc.collect()

        with self.cuda_lock:
            try:

                # Use transformers to generate response
                outputs = self.pipeline(
                    input_records,
                    max_new_tokens=self.max_tokens
                )
                response = outputs[0]["generated_text"][-1]["content"]

                self.log("RESPONSE\n======\n")
                self.log(response)

                return response.strip()
            except Exception as ex:
                print(f"generate_response exception {ex}")

        return ""

    def wait_for_ready(self):
        self.ready_gate.wait()

    def load_model(self):
        """
        Loads the local LLM model using either transformers or llama_cpp.
        """
        if not self.model_loaded:
            try:
                print("Loading text generation model...")
                # Load the model using transformers
                self.pipeline = transformers.pipeline(
                    "text-generation",
                    model=self.model_path,
                    model_kwargs={"torch_dtype": torch.bfloat16},
                    device_map="auto"
                )
            except Exception as ex:
                print(f"load_model exception {ex}")
            finally:
                self.model_loaded = True
                self.ready_gate.set()
