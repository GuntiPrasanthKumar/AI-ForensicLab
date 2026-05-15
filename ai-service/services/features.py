import math
import re
from collections import Counter


def split_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def burstiness(text):
    sentences = split_sentences(text)
    if len(sentences) < 2:
        return 0

    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance


def lexical_diversity(text):
    words = re.findall(r'\w+', text.lower())
    if not words:
        return 0
    unique_words = set(words)
    return len(unique_words) / len(words)


def repetition_score(text):
    words = re.findall(r'\w+', text.lower())
    if not words:
        return 0

    word_counts = Counter(words)
    repeated = sum(count for count in word_counts.values() if count > 1)
    return repeated / len(words)


def shannon_entropy(text):
    words = re.findall(r'\w+', text.lower())
    if not words:
        return 0

    word_counts = Counter(words)
    total = len(words)

    entropy = 0
    for count in word_counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)

    return entropy

def sentence_length_variation_ratio(text):
    sentences = split_sentences(text)
    if len(sentences) < 2:
        return 0

    lengths = [len(s.split()) for s in sentences]
    max_len = max(lengths)
    min_len = min(lengths)

    if max_len == 0:
        return 0

    return (max_len - min_len) / max_len
