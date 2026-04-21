# MP Programming Language 
> A simple, beginner-friendly scripting language built in Python.
> Created by MP Technologies

---

## 🚀 Getting Started

### Run a file
```bash
python mp.py script.mp
```

### Or use the interactive shell
```bash
python mp.py
```

---

## 📖 Cheatsheet

### 💬 Output
```mp
print "Hello World"     // prints text
say "Hello World"       // same as print
```

### 📦 Variables
```mp
x = 10                  // number
name = "KielSir"        // string
print x                 // print a variable
print name
```

### ➕ Math
```mp
x = 1 + 1               // addition
x = 10 - 5              // subtraction
x = 2 * 5               // multiplication
x = 10 / 2              // division
x = sqrt(144)           // 12
x = pow(2, 8)           // 256
x = clamp(15, 0, 10)    // 10
x = randint(1, 100)     // random number
x = round(3.7)          // 4
x = PI                  // 3.14159...
```

### ⌨️ Input
```mp
input name              // asks user, stores in name
print name
```

### ❓ Conditions
```mp
if x == 10 {
    print "x is 10"
}
else {
    print "x is not 10"
}
```

### 🔁 Loops
```mp
x = 0
while x < 5 {
    print x
    x = x + 1
}
```

### 🧩 Functions
```mp
def greet
    say "Hello from MP!"
end

greet               // call the function
```

### 📥 Packages
```mp
mpkg install requests       // installs from pip
```

### 🐍 Raw Python blocks
```mp
pyblock
import requests
r = requests.get("https://example.com")
print(r.status_code)
endpy
```

### 🖥️ System Info
```mp
fetch               // shows OS, CPU, arch, host
```

### 🔧 Define & Open Apps
```mp
#define calculator
open calculator
```

### 📦 Import Modules
```mp
#import math
```

### 🚪 Exit
```mp
exit
```

---

## 🧪 Example Program

```mp
// Hello World
print "Hello, World!"

// Variables and math
x = 10
y = 20
z = x + y
print z

// User input
input name
print "Hello " + name

// Loop
i = 1
while i <= 5 {
    print i
    i = i + 1
}

// Function
def sayHi
    say "Hi from MP!"
end
sayHi
```

---

## 📁 Project Structure

```
MP-Lang/
├── mp.py           ← the interpreter
├── README.md       ← this file
├── LICENSE         ← MIT License
├── mpkg.json       ← installed packages
└── examples/
    ├── hello.mp
    ├── math.mp
    └── loops.mp
```

---

## 📜 License
MIT License — Copyright (c) 2026 KielSir

Free to use, modify, and share. Just give credit! 🥶
