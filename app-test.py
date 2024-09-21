import main

def print_stuff(input):
    print(input)

def interactive_input():
    print("Enter your inputs (type 'done' when finished):")
    inputs = []
    while True:
        user_input = input("> ")
        if user_input.lower() == "done":
            break
        inputs.append(user_input)
    print("\nYou entered:")
    for item in inputs:
        print_stuff(item)

if __name__ == "__main__":
    interactive_input()
