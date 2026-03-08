import argparse
from tasks import LLMTask, EmbeddingTask, AudioTask, ImageTask


def main():
    parser = argparse.ArgumentParser(description="Test runner for FLM models.")
    parser.add_argument('--local', action='store_true', help="Run tests against local FLM server") 
    parser.add_argument('--llm', action='store_true', help="Run LLM tests")
    parser.add_argument('--embedding', action='store_true', help="Run Embedding tests")
    parser.add_argument('--audio', action='store_true', help="Run Audio tests")
    parser.add_argument('--image', action='store_true', help="Run Image tests")
    parser.add_argument('--all', action='store_true', help="Run all available tests")
    parser.add_argument('--gen-lim', type=int, default=-1, help="Maximum number of tokens to generate")
    
    args = parser.parse_args()

    if args.all:
        args.llm = args.embedding = args.audio = args.image = True

    if not any([args.llm, args.embedding, args.audio, args.image]):
        parser.print_help()
        return

    try:
        if args.local:
            run_local = True
            baseurl = "http://localhost:52625/v1"
        else:
            run_local = False
            baseurl = input("Enter the remote server URL (e.g., 130.127.199.196): ")
            port = input("Enter the port number (e.g., 52625): ")
            baseurl = f"http://{baseurl}:{port}/v1"

            # baseurl = "http://130.127.199.196:52625/v1"

        if args.llm:
            LLMTask(baseurl, run_local).run(max_completion_tokens=args.gen_lim)
            
        if args.embedding:
            EmbeddingTask(baseurl).run()
            
        if args.audio:
            AudioTask(baseurl).run()
            
        if args.image:
            ImageTask(baseurl, run_local).run(max_generation_tokens=args.gen_lim)

    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()