import argparse
import json
from pathlib import Path

from datasets import load_dataset


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--subset", default=None)
    ap.add_argument("--split", default="train")
    ap.add_argument("--out_path", default=None)
    ap.add_argument("--instruction_col", default="instruction")
    ap.add_argument("--input_col", default="input")
    ap.add_argument("--output_col", default="output")
    ap.add_argument("--system_col", default=None)
    ap.add_argument("--style", default="roleplay")
    ap.add_argument("--category", default="character_chat")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    if args.subset:
        ds = load_dataset(args.dataset, args.subset, split=args.split)
        default_name = args.subset
    else:
        ds = load_dataset(args.dataset, split=args.split)
        default_name = args.dataset.split("/")[-1]

    if args.out_path:
        out_path = Path(args.out_path)
    else:
        out_dir = Path("datasets/archive")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{default_name}_{args.split}.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for ex in ds:
            system = ""
            if args.system_col:
                value = ex.get(args.system_col)
                if value is not None:
                    system = str(value).strip()

            instruction = str(ex.get(args.instruction_col, "") or "").strip()
            input_text = str(ex.get(args.input_col, "") or "").strip()
            output = str(ex.get(args.output_col, "") or "").strip()

            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            user_content = instruction
            if input_text:
                if user_content:
                    user_content = user_content + "\n\n" + input_text
                else:
                    user_content = input_text
            if user_content:
                messages.append({"role": "user", "content": user_content})

            if output:
                messages.append({"role": "assistant", "content": output})

            if not messages:
                continue

            obj = {
                "messages": messages,
                "style": args.style,
                "category": args.category,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"saved to {out_path}")


if __name__ == "__main__":
    main()

