import ctypes
import pyaudio, audioop, threading, tksvg
from queue import Queue
from tkinter import * # type: ignore
from tkinter import ttk, font
from PIL import ImageTk, Image
from math import log10

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.myproduct.subproduct.version')

root = Tk()
root.title("Howling Monkey")
root.iconbitmap('./assets/monkey_icon.ico')
root.attributes('-topmost', True)

# assets 
# region
calm_monkey_img = Image.open('./assets/monkey_calm.png')
annoyed_monkey_img = Image.open('./assets/monkey_annoyed.png')
agitated_monkey_img = Image.open('./assets/monkey_agitated.png')
howling_monkey_img = Image.open('./assets/monkey_howling.png')
curr_monkey = calm_monkey_img

arc_1_svg = tksvg.SvgImage(file="./assets/arc_1.svg")
arc_2_svg = tksvg.SvgImage(file="./assets/arc_2.svg")
arc_3_svg = tksvg.SvgImage(file="./assets/arc_3.svg")
arc_4_svg = tksvg.SvgImage(file="./assets/arc_4.svg")
arc_5_svg = tksvg.SvgImage(file="./assets/arc_5.svg")
arc_6_svg = tksvg.SvgImage(file="./assets/arc_6.svg")
arc_7_svg = tksvg.SvgImage(file="./assets/arc_7.svg")
arc_8_svg = tksvg.SvgImage(file="./assets/arc_8.svg")
arc_9_svg = tksvg.SvgImage(file="./assets/arc_9.svg")
arc_10_svg = tksvg.SvgImage(file="./assets/arc_10.svg")
arc_11_svg = tksvg.SvgImage(file="./assets/arc_11.svg")
arc_12_svg = tksvg.SvgImage(file="./assets/arc_12.svg")
arc_13_svg = tksvg.SvgImage(file="./assets/arc_13.svg")
arc_14_svg = tksvg.SvgImage(file="./assets/arc_14.svg")

left_leaves_svg = tksvg.SvgImage(file="./assets/left_leaves.svg")
right_leaves_svg = tksvg.SvgImage(file="./assets/right_leaves.svg")
mic_svg = tksvg.SvgImage(file="./assets/mic.svg")
move_svg = tksvg.SvgImage(file="./assets/move.svg", scaletoheight=25)
x_svg = tksvg.SvgImage(file="./assets/x.svg", scaletoheight=20)
# endregion

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
# print(screen_width)
# print(screen_height)

root.geometry('%dx%d+%d+%d' % (320, 150, (screen_width - 320), (screen_height - 210)))
root.minsize(160, 60)
root.maxsize(320, 150)

root.overrideredirect(True)

root.wm_attributes('-transparentcolor', '#402b19')

root.configure(bg="#402b19")
db_queue = Queue()

def move_app(e):
    root.geometry(f'+{e.x_root}+{e.y_root}')

def quitter(e):
    root.quit()
    # root.destroy()

def listen():
    pa = pyaudio.PyAudio()

    stream = pa.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024)
    while True:
        try:
            data = stream.read(1024)
            rms = audioop.rms(data, 2)
            if rms == 0: rms = 1
            db = 20 * log10(rms)
            print(db)
            # print(rms)
            db_queue.put(db)
            

        except Exception as e:
            print(f'\nAudio capture error: {e}')
            break

def update_monkey(db):
    match db:
        # quiet room
        case n if n < 40:
            return calm_monkey_img
        # conversation
        case n if n < 70:
            return annoyed_monkey_img
        # loud radio
        case n if n < 120:
            return agitated_monkey_img
        # loud
        case _:
            return howling_monkey_img

audio_thread = threading.Thread(target=listen, daemon=True)
audio_thread.start()

# fake title bar 
# region
# title_bar = Frame(root, bg="#402b19", relief="flat", bd=0)
# title_bar.pack(expand=0, fill=X)
# title_bar.bind("<B1-Motion>", move_app)

# icon
# icon_img = ImageTk.PhotoImage(Image.open('./assets/monkey_icon_24.png'))
# icon_label = Label(root, image=icon_img, bg='#402b19')
# icon_label.pack(anchor=NW)

# title text
# title_label = Label(title_bar, text="Howling Monkey", bg="DarkSeaGreen4", fg="white")
# title_label.pack(side=LEFT, pady=4)
# endregion

# title close button
x_label = Label(root, image=x_svg, bg='#402b19')
x_label.place(relx=.985, rely=0, anchor=NE)
x_label.bind("<Button-1>", quitter)

# move window button
move_label = Label(root, image=move_svg, bg='#402b19')
move_label.place(relx=0, rely=0, anchor=NW)
move_label.bind("<B1-Motion>", move_app)

# monkey label
monkey_photo = ImageTk.PhotoImage(curr_monkey.resize((100, 100), Image.Resampling.LANCZOS))
monkey_label = Label(root, image=monkey_photo, bg='#402b19')
monkey_label.place(relx=.96, rely=.85, anchor=SE)

# folliage
left_leaves_label = Label(root, image=left_leaves_svg, bg='#402b19')
right_leaves_label = Label(root, image=right_leaves_svg, bg='#402b19')
left_leaves_label.place(relx=0, rely=1, anchor=SW)
right_leaves_label.place(relx=1, rely=1, anchor=SE)
left_leaves_label.lower()
right_leaves_label.lower()

def refresh_monkey():
    global monkey_photo
    latest_db = None
    while not db_queue.empty():
        latest_db = db_queue.get()

    if latest_db is not None:
        curr_monkey = update_monkey(db_queue.get())
        monkey_photo = ImageTk.PhotoImage(curr_monkey)
        monkey_label.configure(image=monkey_photo)
    root.after(50, refresh_monkey)

refresh_monkey()
root.mainloop()