import argparse

def print_stuff(input):
    print(input)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", default=1111)
    args = parser.parse_args()
    print_stuff(args)
