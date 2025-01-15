from whatthetype.whatthetype import trace

def print_stuff(input):
    print(input)

def fake_interactive_input():
    inputs = [1,1.0,"bob"]
    print("\nYou entered:")
    for item in inputs:
        print_stuff(item)

if __name__ == "__main__":
    with trace():
        fake_interactive_input()
