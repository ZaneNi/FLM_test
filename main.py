import argparse
from openai import OpenAI
from tasks import LLMTask, EmbeddingTask, AudioTask, ImageTask


def main():
    parser = argparse.ArgumentParser(description="Test runner for FLM models.")
    parser.add_argument('--llm', action='store_true', help="Run LLM tests")
    parser.add_argument('--embedding', action='store_true', help="Run Embedding tests")
    parser.add_argument('--audio', action='store_true', help="Run Audio tests")
    parser.add_argument('--image', action='store_true', help="Run Image tests")
    parser.add_argument('--all', action='store_true', help="Run all available tests")
    
    args = parser.parse_args()

    if args.all:
        args.llm = args.embedding = args.audio = args.image = True

    if not any([args.llm, args.embedding, args.audio, args.image]):
        parser.print_help()
        return

    try:
        client = OpenAI(base_url="http://localhost:52625/v1", api_key="flm")

        if args.llm:
            LLMTask(client).run(max_completion_tokens=32)
            
        if args.embedding:
            EmbeddingTask(client).run()
            
        if args.audio:
            AudioTask(client).run()
            
        if args.image:
            ImageTask(client).run()

    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()