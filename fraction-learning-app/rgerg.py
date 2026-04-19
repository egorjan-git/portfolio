import tkinter as tk
from tkinter import messagebox
import random
from math import gcd
from fractions import Fraction
from datetime import datetime


class FractionAdditionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обучающая программа по сложению простых дробей")
        self.root.geometry("800x600")


        self.main_container = tk.Frame(root)
        self.main_container.pack(fill="both", expand=True)


        self.nav_frame = tk.Frame(self.main_container, bd=2, relief="groove", padx=10, pady=10)
        self.nav_frame.pack(side="left", fill="y")

        self.main_label = tk.Label(self.nav_frame, text="Выберите опцию:", font=("Arial", 16))
        self.main_label.pack(pady=10)

        self.btn_theory = tk.Button(self.nav_frame, text="Теория", command=self.show_theory, font=("Arial", 14),
                                    width=15)
        self.btn_theory.pack(pady=5)

        self.btn_practice = tk.Button(self.nav_frame, text="Практика", command=self.start_practice, font=("Arial", 14),
                                      width=15)
        self.btn_practice.pack(pady=5)

        self.btn_test = tk.Button(self.nav_frame, text="Тестирование", command=self.start_test, font=("Arial", 14),
                                  width=15)
        self.btn_test.pack(pady=5)


        self.btn_results = tk.Button(self.nav_frame, text="Результаты", command=self.show_results, font=("Arial", 14),
                                     width=15)
        self.btn_results.pack(pady=5)


        self.content_frame = tk.Frame(self.main_container, bd=2, relief="sunken", padx=20, pady=20)
        self.content_frame.pack(side="right", fill="both", expand=True)

    def clear_frame(self):

        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_theory(self):
        self.clear_frame()

        label = tk.Label(self.content_frame, text="Теоретическая часть", font=("Arial", 16))
        label.pack(pady=10)

        btn_examples = tk.Button(self.content_frame, text="Интерактивные примеры", command=self.show_theory_examples,
                                 font=("Arial", 14))
        btn_examples.pack(pady=5)

        btn_info = tk.Button(self.content_frame, text="Справка", command=self.show_theory_info, font=("Arial", 14))
        btn_info.pack(pady=5)

        btn_back = tk.Button(self.content_frame, text="Назад в меню", command=self.clear_frame, font=("Arial", 14))
        btn_back.pack(pady=10)

    def show_theory_examples(self):
        self.clear_frame()

        self.theory_examples = [
            [
                "Пример 1: 1/2 + 1/3",
                "Шаг 1: Найдем общий знаменатель для этих дробей. Для оснований 2 и 3 это 6.",
                "Шаг 2: Приводим дроби к общему знаменателю 6:\n1/2 превращается в 3/6, 1/3 превращается в 2/6.",
                "Шаг 3: Теперь складывем дроби: 3/6 + 2/6 = 5/6."
            ],
            [
                "Пример 2: 2/5 + 3/10",
                "Шаг 1: Общий знаменатель для оснований 5 и 10 – это 10.",
                "Шаг 2: Приводим дроби к общему знаменателю:\n2/5 превращается в 4/10, дробь 3/10 остается без изменений.",
                "Шаг 3: Теперь складывем дроби: 4/10 + 3/10 = 7/10."
            ]
        ]
        self.current_example = 0
        self.current_step = 0

        self.theory_label = tk.Label(
            self.content_frame,
            text=self.theory_examples[self.current_example][self.current_step],
            font=("Arial", 14),
            wraplength=550,
            justify="left"
        )
        self.theory_label.pack(pady=10)

        btn_next = tk.Button(self.content_frame, text="Далее", command=self.next_theory_step, font=("Arial", 14))
        btn_next.pack(pady=5)

        btn_next_example = tk.Button(self.content_frame, text="Следующий пример", command=self.next_theory_example,
                                     font=("Arial", 14))
        btn_next_example.pack(pady=5)

        btn_back = tk.Button(self.content_frame, text="Назад", command=self.show_theory, font=("Arial", 14))
        btn_back.pack(pady=5)

    def next_theory_step(self):
        if self.current_step < len(self.theory_examples[self.current_example]) - 1:
            self.current_step += 1
            self.theory_label.config(text=self.theory_examples[self.current_example][self.current_step])
        else:
            messagebox.showinfo("Информация", "Это был последний шаг. Выберите 'Следующий пример'.")

    def next_theory_example(self):
        if self.current_example < len(self.theory_examples) - 1:
            self.current_example += 1
            self.current_step = 0
            self.theory_label.config(text=self.theory_examples[self.current_example][self.current_step])
        else:
            messagebox.showinfo("Информация", "Это последний пример.")

    def show_theory_info(self):

        info_window = tk.Toplevel(self.root)
        info_window.title("Справка: правила сложения дробей")
        info_window.geometry("600x400")

        text_frame = tk.Frame(info_window)
        text_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 12), yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        info_text = (
            "Справка по сложению простых дробей\n\n"
            "1. Если у дробей одинаковое основание(число снизу, общий знаменатель ), например, 3/8 и 2/8, то просто складываем их числители(числа сверху):\n"
            "   3/8 + 2/8 = 5/8.\n\n"
            "2. Если у дробей разные основания, то дроби нужно привести к общему знаменателю .\n"
            "   Например, чтобы сложить 1/2 и 1/3, надо сделать так, чтобы у дробей было одно и то же основание.\n"
            "   Мы выберем основание 6, потому что 6 делится и на 2, и на 3.\n\n" 
            "   Дробь 1/2: число 6 больше 2 в 3 раза, значит умножаем числитель и знаменатель на 3. Получается дробь 3/6.\n"
            "   Дробь 1/3: число 6 больше 3 в 2 раза, значит умножаем числитель и знаменатель на 2. Получается дробь 2/6.\n\n"
            "   Теперь обе дроби с одинаковым основанием, значит можно сложить их числители, оставив знаменатель без изменений:  3/6 + 2/6 = 5/6.\n\n"
        )

        text_widget.insert("1.0", info_text)
        text_widget.config(state="disabled")

        btn_close = tk.Button(info_window, text="Закрыть", command=info_window.destroy, font=("Arial", 12))
        btn_close.pack(pady=10)

    def start_practice(self):
        self.clear_frame()
        self.score = 0
        self.practice_index = 0
        self.generate_practice_example()

    def generate_practice_example(self):
        if self.practice_index == 50:
            messagebox.showinfo("Практика завершена", "Вы прошли все 50 примеров!")
            self.clear_frame()
            return

        self.practice_index += 1
        self.a, self.b, self.c, self.d = self.generate_fraction()
        text = f"Пример {self.practice_index}: {self.a}/{self.b} + {self.c}/{self.d} = "

        self.practice_label = tk.Label(self.content_frame, text=text, font=("Arial", 14))
        self.practice_label.pack(pady=10)

        self.entry = tk.Entry(self.content_frame, font=("Arial", 14))
        self.entry.pack(pady=5)

        btn_check = tk.Button(self.content_frame, text="Проверить", command=self.check_practice_answer,
                              font=("Arial", 14))
        btn_check.pack(pady=5)

        btn_back_menu = tk.Button(self.content_frame, text="Назад в меню", command=self.clear_frame, font=("Arial", 14))
        btn_back_menu.pack(pady=5)

    def check_practice_answer(self):
        ans = self.entry.get().strip()
        try:
            user_fraction = Fraction(ans)
        except Exception:
            messagebox.showerror("Ошибка ввода", "Введите дробь в формате a/b")
            return

        correct = Fraction(self.a, self.b) + Fraction(self.c, self.d)
        if user_fraction == correct:
            messagebox.showinfo("Верно!", "Ответ правильный!")
        else:
            messagebox.showwarning("Ошибка", f"Неверно! Правильный ответ: {correct}")
        self.clear_frame()
        self.generate_practice_example()

    def start_test(self):
        self.clear_frame()
        self.score = 0
        self.test_index = 0
        self.generate_test_example()

    def generate_test_example(self):
        if self.test_index == 10:
            messagebox.showinfo("Тест завершён", f"Ваш результат: {self.score}/10")
            self.save_result(self.score)
            self.clear_frame()
            return

        self.test_index += 1
        self.a, self.b, self.c, self.d = self.generate_fraction()
        text = f"Пример {self.test_index}: {self.a}/{self.b} + {self.c}/{self.d} = "

        self.test_label = tk.Label(self.content_frame, text=text, font=("Arial", 14))
        self.test_label.pack(pady=10)

        self.entry = tk.Entry(self.content_frame, font=("Arial", 14))
        self.entry.pack(pady=5)

        btn_check = tk.Button(self.content_frame, text="Проверить", command=self.check_test_answer, font=("Arial", 14))
        btn_check.pack(pady=5)

        btn_back_menu = tk.Button(self.content_frame, text="Назад в меню", command=self.clear_frame, font=("Arial", 14))
        btn_back_menu.pack(pady=5)

    def check_test_answer(self):
        ans = self.entry.get().strip()
        try:
            user_fraction = Fraction(ans)
        except Exception:
            messagebox.showerror("Ошибка ввода", "Введите дробь в формате a/b")
            return

        correct = Fraction(self.a, self.b) + Fraction(self.c, self.d)
        if user_fraction == correct:
            self.score += 1
        self.clear_frame()
        self.generate_test_example()

    def save_result(self, score):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("results.txt", "a", encoding="utf-8") as f:
            f.write(f"{now}: {score}/10\n")

    def show_results(self):

        results_window = tk.Toplevel(self.root)
        results_window.title("Результаты тестов")
        results_window.geometry("600x400")

        text_frame = tk.Frame(results_window)
        text_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 12), yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        try:
            with open("results.txt", "r", encoding="utf-8") as f:
                results_data = f.read()
        except FileNotFoundError:
            results_data = "Результаты еще не сохранены."

        text_widget.insert("1.0", results_data)
        text_widget.config(state="disabled")

        btn_close = tk.Button(results_window, text="Закрыть", command=results_window.destroy, font=("Arial", 12))
        btn_close.pack(pady=10)

    def generate_fraction(self):
        a = random.randint(1, 10)
        b = random.randint(2, 10)
        c = random.randint(1, 10)
        d = random.randint(2, 10)
        return a, b, c, d


if __name__ == "__main__":
    root = tk.Tk()
    app = FractionAdditionApp(root)
    root.mainloop()
