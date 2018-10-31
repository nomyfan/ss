'''
This script is used to generate a random password with a given length.
'''
from random import randint


def generate():
    length = input('Length(default 10): ')
    length = int(length) if length.isdigit() and int(length) > 0 else 10
    result = ''
    for x in range(int(length)):
        result += chr(randint(33, 126))
    print(('Take it:\n' if result else '')+result)


if __name__ == '__main__':
    generate()
