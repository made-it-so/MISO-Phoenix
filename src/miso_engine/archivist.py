import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .tools import read_file, write_file
import time

class ArchivistAgent:
    """A specialist agent that uses different LLMs for summarizing and synthesizing."""
    def __init__(self, summarization_llm, synthesis_llm):
        self.summarization_llm = summarization_llm
        self.synthesis_llm = synthesis_llm
        
        # --- ROBUST LOGGING UPGRADE ---
        # This defensively gets the model name, handling different library APIs.
        summarizer_name = getattr(summarization_llm, 'model_name', getattr(summarization_llm, 'model', 'Unknown Summarizer'))
        synthesizer_name = getattr(synthesis_llm, 'model_name', getattr(synthesis_llm, 'model', 'Unknown Synthesizer'))
        
        logging.info(f"Archivist initialized with Summarizer: {summarizer_name} and Synthesizer: {synthesizer_name}")

    def _chunk_text(self, text: str, chunk_size: int = 10000) -> list[str]:
        paragraphs = text.split('\n\n')
        chunks, current_chunk = [], ""
        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += p + "\n\n"
            else:
                chunks.append(current_chunk)
                current_chunk = p + "\n\n"
        chunks.append(current_chunk)
        return chunks

    def _summarize_chunk(self, chunk: str) -> str:
        """Uses the designated summarization LLM."""
        prompt = ChatPromptTemplate.from_template(
            "You are a summarization expert. Extract key events, architectural decisions, and critical failures from the following text. Be concise.\n\n---\n\n{chunk}"
        )
        chain = prompt | self.summarization_llm | StrOutputParser()
        return chain.invoke({"chunk": chunk})

    def _synthesize_summaries(self, summaries: list[str], goal: str) -> str:
        """Uses the designated synthesis LLM."""
        summaries_str = "\n\n---\n\n".join(summaries)
        prompt = ChatPromptTemplate.from_template(
            """
            You are an AI Systems Architect and technical writer. Synthesize the provided summaries into a final, comprehensive architectural design document that fulfills the user's goal.

            **User Goal:**
            {goal}

            **Summaries of Project History:**
            {summaries}

            **Your Task:**
            Generate the final, complete Markdown document.
            """
        )
        chain = prompt | self.synthesis_llm | StrOutputParser()
        return chain.invoke({"goal": goal, "summaries": summaries_str})

    def run(self, input_file: str, output_file: str, goal: str):
        logging.info(f"Archivist Mission Started: Reading and chunking '{input_file}'...")
        try:
            full_text = read_file(input_file)
        except Exception as e:
            logging.error(f"Failed to read the history file. Error: {e}"); return

        chunks = self._chunk_text(full_text)
        logging.info(f"Text successfully split into {len(chunks)} chunks.")

        summaries = []
        for i, chunk in enumerate(chunks):
            logging.info(f"Summarizing chunk {i+1}/{len(chunks)}...")
            summary = self._summarize_chunk(chunk)
            summaries.append(summary)
            logging.info(f"Chunk {i+1} summary complete. Pausing for 2 seconds...")
            time.sleep(2)

        logging.info("All chunks summarized. Synthesizing the final document...")
        final_document = self._synthesize_summaries(summaries, goal)
        
        write_file(output_file, final_document)
        logging.info(f"Final document '{output_file}' has been created successfully.")
