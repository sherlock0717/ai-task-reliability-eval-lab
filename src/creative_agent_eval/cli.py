import argparse, json
from .registry import validate_registry

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["validate-registry"])
    args=p.parse_args()
    if args.command=="validate-registry": print(json.dumps(validate_registry(),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
