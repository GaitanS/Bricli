import argparse

def main():
    parser = argparse.ArgumentParser(description="Say hello")
    parser.add_argument("--name", default="World", help="Name to greet")
    args = parser.parse_args()

    print(f"Hello, {args.name}! This is running from your custom local skill.")

if __name__ == "__main__":
    main()
