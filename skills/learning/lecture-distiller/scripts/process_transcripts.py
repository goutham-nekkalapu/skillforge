#!/usr/bin/env python3
"""
Transcript pre-processor for Lecture Distiller.

Cleans video transcripts, extracts key concepts, and reports compression
statistics. Useful as a first pass before handing transcripts to the skill.

Usage:
    python process_transcripts.py <directory>
    python process_transcripts.py <directory> --pattern "lecture_*.md"
    python process_transcripts.py <file1.md> <file2.md>
"""

import argparse
import glob
import os
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple


class TranscriptProcessor:
    """Process video transcripts to extract key information."""

    FILLER_WORDS = {
        "um", "uh", "like", "you know", "actually", "basically",
        "literally", "right", "okay", "so", "well", "I mean",
        "kind of", "sort of", "you see", "you know what I mean",
    }

    CONCEPT_INDICATORS = {
        "important", "key", "remember", "note that", "critical",
        "essential", "fundamental", "significant", "main point",
        "takeaway", "in summary", "to summarize", "the idea is",
    }

    STOP_WORDS = {
        "the", "is", "at", "which", "on", "a", "an", "as", "are",
        "was", "were", "in", "to", "for", "of", "and", "or", "but",
        "this", "that", "with", "from", "not", "have", "has", "had",
        "will", "would", "could", "should", "can", "may", "might",
        "been", "being", "do", "does", "did", "just", "than", "then",
        "also", "very", "about", "into", "over", "such", "its", "only",
    }

    def clean_transcript(self, text: str) -> str:
        """Remove filler words and clean up transcript text."""
        cleaned = text
        for filler in self.FILLER_WORDS:
            pattern = r"\b" + re.escape(filler) + r"\b"
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\s+", " ", cleaned)

        sentences = cleaned.split(". ")
        cleaned = ". ".join(s.strip().capitalize() for s in sentences if s.strip())

        return cleaned.strip()

    def extract_key_concepts(self, text: str) -> List[str]:
        """Extract sentences containing key concept indicators."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        key_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(ind in sentence_lower for ind in self.CONCEPT_INDICATORS):
                stripped = sentence.strip()
                if stripped:
                    key_sentences.append(stripped)

        return key_sentences

    def find_code_blocks(self, text: str) -> List[Dict]:
        """Extract code blocks from transcript."""
        blocks = []
        for match in re.finditer(r"```[\w]*\n(.*?)\n```", text, re.DOTALL):
            blocks.append({"code": match.group(1), "type": "block"})
        for match in re.finditer(r"`([^`]+)`", text):
            blocks.append({"code": match.group(1), "type": "inline"})
        return blocks

    def identify_topics(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """Identify main topics based on word frequency."""
        words = re.findall(r"\b[a-z]+\b", text.lower())
        filtered = [w for w in words if w not in self.STOP_WORDS and len(w) > 3]
        return Counter(filtered).most_common(top_n)

    def create_summary(self, text: str, max_length: int = 500) -> str:
        """Create a brief summary from key sentences."""
        key_sentences = self.extract_key_concepts(text)

        if not key_sentences:
            sentences = re.split(r"(?<=[.!?])\s+", text)[:3]
            summary = " ".join(sentences)
        else:
            summary = " ".join(key_sentences[:3])

        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."

        return summary

    def process_file(self, filepath: str) -> Dict:
        """Process a single transcript file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "original_length": len(content),
            "cleaned_text": self.clean_transcript(content),
            "key_concepts": self.extract_key_concepts(content),
            "code_blocks": self.find_code_blocks(content),
            "main_topics": self.identify_topics(content),
            "summary": self.create_summary(content),
        }

    def process_directory(self, directory: str, pattern: str = "v*.md") -> List[Dict]:
        """Process transcript files matching a glob pattern in a directory."""
        search = os.path.join(directory, pattern)
        files = sorted(glob.glob(search))

        if not files:
            print(f"No files matching '{pattern}' in {directory}", file=sys.stderr)
            return []

        return [self.process_file(f) for f in files]

    def generate_outline(self, results: List[Dict]) -> str:
        """Generate a course outline from processed transcripts."""
        lines = ["# Course Outline\n"]

        for i, r in enumerate(results, 1):
            lines.append(f"## Video {i}: {r['filename']}")
            lines.append(f"**Summary:** {r['summary']}\n")

            if r["main_topics"]:
                lines.append("**Main Topics:**")
                for topic, freq in r["main_topics"][:5]:
                    lines.append(f"- {topic} ({freq} mentions)")
                lines.append("")

            if r["code_blocks"]:
                lines.append(f"**Contains {len(r['code_blocks'])} code examples**\n")

        return "\n".join(lines)

    def print_stats(self, results: List[Dict]) -> None:
        """Print compression statistics."""
        total_original = sum(r["original_length"] for r in results)
        total_cleaned = sum(len(r["cleaned_text"]) for r in results)

        if total_original == 0:
            return

        compression = (1 - total_cleaned / total_original) * 100
        print(f"\n--- Stats ---")
        print(f"Files processed: {len(results)}")
        print(f"Original: {total_original:,} chars")
        print(f"Cleaned:  {total_cleaned:,} chars")
        print(f"Compression: {compression:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Pre-process video transcripts for Lecture Distiller."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Directory to scan or individual transcript files.",
    )
    parser.add_argument(
        "--pattern",
        default="v*.md",
        help='Glob pattern for transcripts when a directory is given (default: "v*.md").',
    )
    parser.add_argument(
        "--outline",
        action="store_true",
        help="Print a generated course outline.",
    )
    args = parser.parse_args()

    processor = TranscriptProcessor()
    results = []

    for path in args.paths:
        if os.path.isdir(path):
            results.extend(processor.process_directory(path, args.pattern))
        elif os.path.isfile(path):
            results.append(processor.process_file(path))
        else:
            print(f"Skipping: {path} (not found)", file=sys.stderr)

    if not results:
        print("No transcripts processed.", file=sys.stderr)
        sys.exit(1)

    if args.outline:
        print(processor.generate_outline(results))

    processor.print_stats(results)


if __name__ == "__main__":
    main()
