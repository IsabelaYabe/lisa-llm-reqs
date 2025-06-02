import re

if __name__ == "__main__":
    s = "Hello?? Is anyone there??"
    
    busca = re.findall("\w+??", s)
    print(busca)
    