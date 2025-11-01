import os
from datasets import load_dataset

# 1️⃣ Create samples folder
SAMPLES_DIR = os.path.join(os.getcwd(), "backend", "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)
print(f"📂 Saving samples to: {SAMPLES_DIR}")

# 2️⃣ Load Samsum dataset
print("⬇️ Downloading real conversational samples (SAMSum dataset)...")
dataset = load_dataset("samsum", split="train")

# 3️⃣ Pick a few long samples
NUM_SAMPLES = 3
for i in range(NUM_SAMPLES):
    sample = dataset[i]
    dialogue = sample["dialogue"]
    summary = sample["summary"]

    text_path = os.path.join(SAMPLES_DIR, f"meeting_{i+1}.txt")
    summary_path = os.path.join(SAMPLES_DIR, f"meeting_{i+1}_summary.txt")

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(dialogue)

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"\n✅ Sample {i+1} saved:")
    print(f"   🗒 Transcript: {text_path}")
    print(f"   🧾 Summary: {summary_path}")

print("\n✨ Done! You can now test:")
print("   POST /summarize/text with one of the meeting_X.txt files.")
