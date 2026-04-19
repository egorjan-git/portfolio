import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DATA_DIR = './data'
state = {
    "dfs": {},
    "current_edit_df": None,
    "canvas": None,
    "edit_tree": None,
    "edit_tree_name": None,
    "root": None,
    "comboboxes": [],
    "edit_df_cb": None,
    "rep_df_cb": None,
    "viz_df_cb": None,
}

def convert_sheets_to_pickle(excel_path, output_dir=DATA_DIR):
    """
    Функция конвертации всех листов Excel-файла в pickle-файлы
    Автор: Бохан Д.В.
    Вход: excel_path - путь к Excel-файлу, output_dir - папка для сохранения
    Выход: отсутствует (сохраняет файлы)
    """
    os.makedirs(output_dir, exist_ok=True)
    sheets = pd.read_excel(excel_path, sheet_name=None)
    for name, df in sheets.items():
        df.columns = df.columns.str.strip()
        df.to_pickle(os.path.join(output_dir, f"{name}.pkl"))
    messagebox.showinfo("Готово", "Справочники сохранены.")

def load_dataframes(data_dir=DATA_DIR):
    """
    Функция загрузки всех pickle-файлов в словарь DataFrame
    Автор: Казаков Е.А.
    Вход: data_dir - папка с pickle
    Выход: dict с DataFrame
    """
    dfs = {}
    if not os.path.isdir(data_dir):
        return dfs
    for fname in os.listdir(data_dir):
        if fname.lower().endswith('.pkl'):
            key = os.path.splitext(fname)[0]
            try:
                dfs[key] = pd.read_pickle(os.path.join(data_dir, fname))
            except Exception:
                pass
    return dfs


def resolve_column(df, choice):
    """
    Функция поиска и проверки существования колонки в DataFrame
    Автор: Валиев Т.М.
    Вход: df - DataFrame, choice - название колонки
    Выход: str - название колонки
    """
    c = choice.strip()
    if c in df.columns:
        return c
    raise KeyError(f"Колонка '{choice}' не найдена")


def refresh_all_comboboxes():
    """
    Функция обновления всех combobox интерфейса после загрузки/смены данных
    Автор: Бохан Д.В.
    Вход: отсутствует
    Выход: отсутствует
    """
    lists = df_list()
    if state.get("viz_df_cb"):
        state["viz_df_cb"]['values'] = lists
        state["viz_df_cb"].set('')
    if state.get("rep_df_cb"):
        state["rep_df_cb"]['values'] = lists
        state["rep_df_cb"].set('')
    if state.get("edit_df_cb"):
        state["edit_df_cb"]['values'] = lists
        state["edit_df_cb"].set('')

def report_age_threshold(df, age_col, min_age, cols=None):
    """
    Функция отбора строк по порогу возраста
    Автор: Валиев Т.М.
    Вход: df - DataFrame, age_col - колонка возраста, min_age - порог, cols - опционально
    Выход: DataFrame
    """
    col = resolve_column(df, age_col)
    mask = pd.to_numeric(df[col], errors='coerce') >= min_age
    res = df.loc[mask]
    if cols:
        res = res[[resolve_column(df, c) for c in cols]]
    return res

def report_category_filter(df, category_col, allowed_values, cols=None):
    """
    Функция фильтрации по категории
    Автор: Казаков Е.А.
    Вход: df - DataFrame, category_col - колонка, allowed_values - список, cols - опционально
    Выход: DataFrame
    """
    col = resolve_column(df, category_col)
    mask = df[col].astype(str).isin(allowed_values)
    res = df.loc[mask]
    if cols:
        res = res[[resolve_column(df, c) for c in cols]]
    return res

def report_date_range(df, date_col, start_date, end_date, cols=None):
    """
    Функция фильтрации по диапазону дат
    Автор: Валиев Т.М.
    Вход: df - DataFrame, date_col - колонка даты, start_date, end_date, cols - опционально
    Выход: DataFrame
    """
    col = resolve_column(df, date_col)
    dates = pd.to_datetime(df[col], errors='coerce')
    mask = dates.between(start_date, end_date)
    res = df.loc[mask]
    if cols:
        res = res[[resolve_column(df, c) for c in cols]]
    return res

def report_pivot(df, index, columns, values, aggfunc='sum', fill_value=None):
    """
    Функция построения сводной таблицы (pivot)
    Автор: Валиев Т.М.
    Вход: df - DataFrame, index, columns, values, aggfunc, fill_value
    Выход: DataFrame
    """
    idx = [resolve_column(df, c) for c in index] if index else []
    cols = [resolve_column(df, c) for c in columns] if columns else []
    vals = [resolve_column(df, c) for c in values] if values else []
    return pd.pivot_table(df, index=idx, columns=cols, values=vals,
                          aggfunc=aggfunc, fill_value=fill_value)

def main():
    """
    Точка входа, инициализация всего приложения
    Автор: Казаков Е.А.
    Вход: отсутствует
    Выход: отсутствует
    """
    root = tk.Tk()
    state["root"] = root
    root.title("Анализ и отчёты")
    root.geometry("1000x800")
    root.configure(bg='#f0f0f0')

    state["dfs"] = load_dataframes()

    style = ttk.Style(root)
    style.theme_use('default')
    style.configure('TButton', background='#4CAF50', foreground='white', padding=6, font=('Arial', 10))
    style.map('TButton', background=[('active', '#45a049')])
    style.configure('Treeview', rowheight=25, font=('Arial', 10))
    style.configure('TLabel', font=('Arial', 10))

    nb = ttk.Notebook(root)
    nb.pack(fill='both', expand=True, padx=10, pady=10)

    tab_viz = ttk.Frame(nb)
    tab_reports = ttk.Frame(nb)
    tab_edit = ttk.Frame(nb)
    tab_settings = ttk.Frame(nb)

    nb.add(tab_viz, text='Визуализация')
    nb.add(tab_reports, text='Текстовые отчёты')
    nb.add(tab_edit, text='Редактировать')
    nb.add(tab_settings, text='Настройки интерфейса')

    build_viz_tab(tab_viz, root)
    build_reports_tab(tab_reports, root)
    build_edit_tab(tab_edit, root)
    build_settings_tab(tab_settings, root)

    root.mainloop()

def df_list():
    """
    Функция, возвращающая список справочников для выпадающих списков
    Автор: Бохан Д.В.
    Вход: отсутствует
    Выход: list
    """
    return [f"{i+1}. {k}" for i, k in enumerate(state["dfs"].keys())]

def build_viz_tab(tab, root):
    """
    Функция построения вкладки визуализации
    Автор: Казаков Е.А.
    Вход: tab - объект вкладки, root - главное окно
    Выход: отсутствует
    """
    ttk.Button(tab, text="→ Excel→pickle", command=lambda: on_convert(root)).pack(pady=8)
    ttk.Label(tab, text="Справочник:").pack(anchor='w', padx=12)
    viz_df_cb = ttk.Combobox(tab, values=df_list(), state='readonly')
    viz_df_cb.pack(fill='x', padx=12, pady=2)
    state["viz_df_cb"] = viz_df_cb

    viz_df_cb.bind('<<ComboboxSelected>>', lambda e: update_columns(viz_df_cb, x_cb, y_cb))

    ttk.Label(tab, text="Тип графика:").pack(anchor='w', padx=12)
    viz_type = tk.StringVar(value='histbox')
    for txt, val in [('Гистограмма','hist'),('Гист+Box','histbox'),('Scatter','scatter')]:
        ttk.Radiobutton(tab, text=txt, variable=viz_type, value=val).pack(anchor='w', padx=20)

    ttk.Label(tab, text="Ось X:").pack(anchor='w', padx=12)
    x_cb = ttk.Combobox(tab, state='readonly'); x_cb.pack(fill='x', padx=12, pady=2)
    ttk.Label(tab, text="Ось Y:").pack(anchor='w', padx=12)
    y_cb = ttk.Combobox(tab, state='readonly'); y_cb.pack(fill='x', padx=12, pady=2)
    ttk.Button(tab, text="🔹 Построить", command=lambda: draw_viz(tab, viz_df_cb, x_cb, y_cb, viz_type)).pack(pady=12)
    canvas_fr = tk.Frame(tab, bd=2, relief='sunken')
    canvas_fr.pack(fill='both', expand=True, padx=12, pady=12)
    state["canvas_fr"] = canvas_fr

def update_columns(viz_df_cb, x_cb, y_cb):
    """
    Функция обновления выпадающих списков выбора осей
    Автор: Бохан Д.В.
    Вход: viz_df_cb, x_cb, y_cb
    Выход: отсутствует
    """
    if not viz_df_cb.get():
        return
    name = viz_df_cb.get().split('. ',1)[1]
    cols = [f"{i+1}. {c}" for i, c in enumerate(state["dfs"][name].columns)]
    x_cb['values'], y_cb['values'] = cols, cols
    if cols:
        x_cb.current(0)
        y_cb.current(min(1, len(cols)-1))

def draw_viz(tab, viz_df_cb, x_cb, y_cb, viz_type):
    """
    Функция построения графика на вкладке визуализации
    Автор: Казаков Е.А.
    Вход: tab, viz_df_cb, x_cb, y_cb, viz_type
    Выход: отсутствует
    """
    if not viz_df_cb.get() or not x_cb.get():
        return
    name = viz_df_cb.get().split('. ',1)[1]
    df = state["dfs"][name]
    mode = viz_type.get()
    xcol = resolve_column(df, x_cb.get().split('. ',1)[1])
    fig = plt.Figure(figsize=(8,5), tight_layout=True)
    if mode == 'hist':
        ax = fig.add_subplot()
        data = pd.to_numeric(df[xcol], errors='coerce').dropna()
        ax.hist(data, bins=10, edgecolor='black')
        ax.set_title(f'Гистограмма: {xcol}')
    elif mode == 'histbox':
        ax1 = fig.add_subplot(1,2,1)
        ax2 = fig.add_subplot(1,2,2)
        data = pd.to_numeric(df[xcol], errors='coerce').dropna()
        ax1.hist(data, bins=10, edgecolor='black'); ax1.set_title(f'Гистограмма: {xcol}')
        ax2.boxplot(data, vert=False); ax2.set_title(f'Boxplot: {xcol}')
    else:
        if not y_cb.get():
            return
        ycol = resolve_column(df, y_cb.get().split('. ',1)[1])
        x = pd.to_numeric(df[xcol], errors='coerce')
        y = pd.to_numeric(df[ycol], errors='coerce')
        mask = x.notna() & y.notna()
        ax = fig.add_subplot()
        ax.scatter(x[mask], y[mask], alpha=0.7)
        ax.set_xlabel(xcol); ax.set_ylabel(ycol)
        ax.set_title(f'Scatter: {ycol} vs {xcol}')
    if state["canvas"]:
        state["canvas"].get_tk_widget().destroy()
    state["canvas"] = FigureCanvasTkAgg(fig, master=state["canvas_fr"])
    state["canvas"].draw()
    state["canvas"].get_tk_widget().pack(fill='both', expand=True)

def on_convert(root):
    """
    Функция-обработчик конвертации Excel в pickle
    Автор: Валиев Т.М.
    Вход: root
    Выход: отсутствует
    """
    path = filedialog.askopenfilename(filetypes=[('Excel','*.xlsx *.xls')])
    if path:
        convert_sheets_to_pickle(path)
        state["dfs"] = load_dataframes()
        refresh_all_comboboxes()

def build_reports_tab(tab, root):
    """
    Функция построения вкладки текстовых отчётов
    Автор: Валиев Т.М.
    Вход: tab, root
    Выход: отсутствует
    """
    ttk.Button(tab, text="→ Excel→pickle", command=lambda: on_convert(root)).pack(pady=8)
    ttk.Label(tab, text="Справочник:").pack(anchor='w', padx=12)
    rep_df_cb = ttk.Combobox(tab, values=df_list(), state='readonly')
    rep_df_cb.pack(fill='x', padx=12, pady=2)
    state["rep_df_cb"] = rep_df_cb

    ttk.Label(tab, text="Тип отчета:").pack(anchor='w', padx=12)
    types = ["Возраст","Категория","Диапазон дат","Сводная таблица","Описание"]
    rep_type_cb = ttk.Combobox(tab, values=types, state='readonly')
    rep_type_cb.pack(fill='x', padx=12, pady=2)
    params_fr = tk.Frame(tab)
    params_fr.pack(fill='x', padx=12, pady=10)
    ttk.Button(tab, text="📑 Генерировать", command=lambda: gen_report(tab, rep_df_cb, rep_type_cb, params_fr)).pack(pady=8)
    rep_table = ttk.Treeview(tab, show="headings")
    rep_table.pack(fill='both', expand=True, padx=12, pady=10)
    rep_scroll = ttk.Scrollbar(tab, orient="vertical", command=rep_table.yview)
    rep_table.configure(yscrollcommand=rep_scroll.set)
    rep_scroll.pack(side='right', fill='y')

    state["rep_params"] = (rep_df_cb, rep_type_cb, params_fr, rep_table)
    rep_type_cb.bind('<<ComboboxSelected>>', lambda e: update_rep_params(rep_df_cb, rep_type_cb, params_fr))

def update_rep_params(rep_df_cb, rep_type_cb, params_fr):
    """
    Функция обновления параметров для генерации отчёта
    Автор: Казаков Е.А.
    Вход: rep_df_cb, rep_type_cb, params_fr
    Выход: отсутствует
    """
    for w in params_fr.winfo_children():
        w.destroy()
    rtype = rep_type_cb.get()
    try:
        name = rep_df_cb.get().split('. ',1)[1]
        df = state["dfs"][name]
        cols = list(df.columns)
    except Exception:
        cols = []
    row = 0
    if rtype != "Описание":
        tk.Label(params_fr, text="Колонки:").grid(row=row, column=0, sticky='w')
        cols_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        cols_cb.grid(row=row, column=1, sticky='ew', pady=2)
        params_fr.cols_cb = cols_cb
        row += 1
    if rtype == "Возраст":
        tk.Label(params_fr, text="Колонка возраста:").grid(row=row, column=0, sticky='w')
        age_col_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        age_col_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Мин возраст:").grid(row=row, column=0, sticky='w')
        min_age_ent = tk.Entry(params_fr)
        min_age_ent.insert(0, "0")
        min_age_ent.grid(row=row, column=1, sticky='ew'); row+=1
        params_fr.age_col_cb = age_col_cb
        params_fr.min_age_ent = min_age_ent
    elif rtype == "Категория":
        tk.Label(params_fr, text="Колонка:").grid(row=row, column=0, sticky='w')
        cat_col_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        cat_col_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Значения:").grid(row=row, column=0, sticky='w')
        cat_vals_cb = tk.Listbox(params_fr, selectmode='multiple', height=5, exportselection=False)
        cat_vals_cb.grid(row=row, column=1, sticky='ew'); row+=1
        def update_cat_vals(*_):
            col = cat_col_cb.get()
            if col in df:
                vals = sorted(map(str, df[col].dropna().unique()))
                cat_vals_cb.delete(0, tk.END)
                for v in vals:
                    cat_vals_cb.insert(tk.END, v)
        cat_col_cb.bind('<<ComboboxSelected>>', update_cat_vals)
        params_fr.cat_col_cb = cat_col_cb
        params_fr.cat_vals_cb = cat_vals_cb
    elif rtype == "Диапазон дат":
        tk.Label(params_fr, text="Колонка даты:").grid(row=row, column=0, sticky='w')
        date_col_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        date_col_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Начало:").grid(row=row, column=0, sticky='w')
        start_cb = ttk.Combobox(params_fr, values=[], state='readonly')
        start_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Конец:").grid(row=row, column=0, sticky='w')
        end_cb = ttk.Combobox(params_fr, values=[], state='readonly')
        end_cb.grid(row=row, column=1, sticky='ew'); row+=1
        def update_dates(*_):
            col = date_col_cb.get()
            if col in df:
                vals = sorted(pd.to_datetime(df[col], errors='coerce').dropna().unique())
                svals = [str(v)[:10] for v in vals]
                start_cb['values'] = svals
                end_cb['values'] = svals
                if svals:
                    start_cb.current(0)
                    end_cb.current(len(svals)-1)
        date_col_cb.bind('<<ComboboxSelected>>', update_dates)
        params_fr.date_col_cb = date_col_cb
        params_fr.start_cb = start_cb
        params_fr.end_cb = end_cb
    elif rtype == "Сводная таблица":
        tk.Label(params_fr, text="Индексы:").grid(row=row, column=0, sticky='w')
        idx_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        idx_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Колонки:").grid(row=row, column=0, sticky='w')
        piv_cols_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        piv_cols_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Значения:").grid(row=row, column=0, sticky='w')
        piv_vals_cb = ttk.Combobox(params_fr, values=cols, state='readonly')
        piv_vals_cb.grid(row=row, column=1, sticky='ew'); row+=1
        tk.Label(params_fr, text="Агрегат:").grid(row=row, column=0, sticky='w')
        agg_cb = ttk.Combobox(params_fr, values=['sum','mean','count','min','max'], state='readonly')
        agg_cb.grid(row=row, column=1, sticky='ew')
        params_fr.idx_cb = idx_cb
        params_fr.piv_cols_cb = piv_cols_cb
        params_fr.piv_vals_cb = piv_vals_cb
        params_fr.agg_cb = agg_cb
    params_fr.columnconfigure(1, weight=1)

def gen_report(tab, rep_df_cb, rep_type_cb, params_fr):
    """
    Функция генерации выбранного текстового отчёта
    Автор: Валиев Т.М.
    Вход: tab, rep_df_cb, rep_type_cb, params_fr
    Выход: отсутствует
    """
    rep_table = state["rep_params"][3]
    rep_table.delete(*rep_table.get_children())
    if not rep_df_cb.get():
        return
    name = rep_df_cb.get().split('. ',1)[1]
    df = state["dfs"][name]
    rtype = rep_type_cb.get()
    try:
        if rtype == "Возраст":
            age_col = params_fr.age_col_cb.get()
            min_age = int(params_fr.min_age_ent.get())
            col = params_fr.cols_cb.get() if hasattr(params_fr, 'cols_cb') and params_fr.cols_cb.get() else None
            cols = [col] if col else None
            res = report_age_threshold(df, age_col, min_age, cols)
        elif rtype == "Категория":
            cat_col = params_fr.cat_col_cb.get()
            vals = [params_fr.cat_vals_cb.get(i) for i in params_fr.cat_vals_cb.curselection()]
            col = params_fr.cols_cb.get() if hasattr(params_fr, 'cols_cb') and params_fr.cols_cb.get() else None
            cols = [col] if col else None
            res = report_category_filter(df, cat_col, vals, cols)
        elif rtype == "Диапазон дат":
            date_col = params_fr.date_col_cb.get()
            start = params_fr.start_cb.get()
            end = params_fr.end_cb.get()
            col = params_fr.cols_cb.get() if hasattr(params_fr, 'cols_cb') and params_fr.cols_cb.get() else None
            cols = [col] if col else None
            res = report_date_range(df, date_col, start, end, cols)
        elif rtype == "Сводная таблица":
            idx = [params_fr.idx_cb.get()] if hasattr(params_fr, 'idx_cb') and params_fr.idx_cb.get() else None
            pivc = [params_fr.piv_cols_cb.get()] if hasattr(params_fr, 'piv_cols_cb') and params_fr.piv_cols_cb.get() else None
            pivv = [params_fr.piv_vals_cb.get()] if hasattr(params_fr, 'piv_vals_cb') and params_fr.piv_vals_cb.get() else None
            aggfunc = params_fr.agg_cb.get() if hasattr(params_fr, 'agg_cb') and params_fr.agg_cb.get() else 'sum'
            res = report_pivot(df, idx, pivc, pivv, aggfunc=aggfunc)
        else:
            special_cols = [
                "Сколько приёмов пищи вы обычно совершаете за день?",
                "Сколько у вас тренировок в неделю?",
                "Укажите ваш возраст"
            ]
            cols_to_describe = set()
            if hasattr(params_fr, 'cols_cb') and params_fr.cols_cb.get():
                cols_to_describe.add(params_fr.cols_cb.get())
            else:
                for c in df.select_dtypes(include='number').columns:
                    cols_to_describe.add(c)
                for sc in special_cols:
                    if sc in df.columns:
                        cols_to_describe.add(sc)
            real_cols = [c for c in cols_to_describe if c in df.columns]
            if real_cols:
                res = df[real_cols].apply(pd.to_numeric, errors='coerce').describe()
            else:
                res = pd.DataFrame()
    except Exception as e:
        messagebox.showerror("Ошибка генерации отчёта", str(e))
        return
    if isinstance(res, pd.DataFrame) or isinstance(res, pd.Series):
        if isinstance(res, pd.Series):
            res = res.to_frame()
        show_table(rep_table, res)
    else:
        messagebox.showinfo("Отчёт", str(res))

def show_table(tree, df):
    """
    Функция вывода таблицы отчёта в Treeview
    Автор: Валиев Т.М.
    Вход: tree - Treeview, df - DataFrame
    Выход: отсутствует
    """
    tree.delete(*tree.get_children())
    if isinstance(df.columns, pd.MultiIndex):
        columns = [" / ".join(map(str, c)) for c in df.columns.values]
    else:
        columns = list(map(str, df.columns))
    if "index" not in columns and not df.index.equals(pd.RangeIndex(len(df))):
        columns = ["index"] + columns
        df = df.reset_index()
    tree["columns"] = columns
    for c in columns:
        tree.heading(c, text=str(c))
        tree.column(c, width=130, anchor='center')
    for _, row in df.iterrows():
        vals = list(map(str, row.values))
        tree.insert('', 'end', values=vals)

def build_edit_tab(tab, root):
    """
    Функция построения вкладки редактирования данных
    Автор: Бохан Д.В.
    Вход: tab, root
    Выход: отсутствует
    """
    ttk.Label(tab, text="Справочник для редактирования:").pack(anchor='w', padx=12, pady=5)
    edit_df_cb = ttk.Combobox(tab, values=df_list(), state='readonly')
    edit_df_cb.pack(fill='x', padx=12, pady=2)
    state["edit_df_cb"] = edit_df_cb

    tree_frame = tk.Frame(tab)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=10)
    btn_fr = tk.Frame(tab)
    btn_fr.pack(pady=5)
    ttk.Button(btn_fr, text="💾 Сохранить", command=lambda: save_edit(tree_frame)).pack(side='left', padx=5)
    ttk.Button(btn_fr, text="📤 Экспорт", command=lambda: export_to_excel()).pack(side='left', padx=5)
    edit_df_cb.bind('<<ComboboxSelected>>', lambda e: load_edit_table(edit_df_cb, tree_frame))

def load_edit_table(edit_df_cb, tree_frame):
    """
    Функция загрузки выбранной таблицы в редактор
    Автор: Бохан Д.В.
    Вход: edit_df_cb, tree_frame
    Выход: отсутствует
    """
    if not edit_df_cb.get():
        return
    name = edit_df_cb.get().split('. ',1)[1]
    df = state["dfs"][name]
    state["current_edit_df"] = name
    for w in tree_frame.winfo_children():
        w.destroy()
    cols = list(df.columns)
    edit_tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
    for c in cols:
        edit_tree.heading(c, text=c)
        edit_tree.column(c, width=100)
    for i, row in df.iterrows():
        edit_tree.insert('', 'end', iid=str(i), values=[row[c] for c in cols])
    edit_tree.pack(fill='both', expand=True)
    edit_tree.bind('<Double-1>', lambda event: on_edit_cell(event, edit_tree, tree_frame))
    state["edit_tree"] = edit_tree

def on_edit_cell(event, edit_tree, tree_frame):
    """
    Функция-обработчик для редактирования ячейки
    Автор: Бохан Д.В.
    Вход: event, edit_tree, tree_frame
    Выход: отсутствует
    """
    region = edit_tree.identify('region', event.x, event.y)
    if region != 'cell':
        return
    row_id = edit_tree.identify_row(event.y)
    col_id = edit_tree.identify_column(event.x)
    col_idx = int(col_id.replace('#','')) - 1
    x, y, w, h = edit_tree.bbox(row_id, col_id)
    val = edit_tree.set(row_id, edit_tree['columns'][col_idx])
    entry = tk.Entry(tree_frame)
    entry.place(x=x, y=y, width=w, height=h)
    entry.insert(0, val); entry.focus()
    def on_out(e):
        edit_tree.set(row_id, edit_tree['columns'][col_idx], entry.get())
        entry.destroy()
    entry.bind('<FocusOut>', on_out)

def save_edit(tree_frame):
    """
    Функция сохранения изменений в редактируемом справочнике
    Автор: Казаков Е.А.
    Вход: tree_frame
    Выход: отсутствует
    """
    name = state["current_edit_df"]
    if not name or state["edit_tree"] is None:
        messagebox.showwarning("Ошибка", "Выберите справочник для сохранения.")
        return
    cols = list(state["dfs"][name].columns)
    data = [state["edit_tree"].item(r)['values'] for r in state["edit_tree"].get_children()]
    new_df = pd.DataFrame(data, columns=cols)
    path = os.path.join(DATA_DIR, f"{name}.pkl")
    try:
        new_df.to_pickle(path)
    except Exception as e:
        messagebox.showerror("Ошибка сохранения", str(e))
        return
    state["dfs"][name] = new_df
    messagebox.showinfo("Сохранено", f"Изменения сохранены в {path}")

def export_to_excel():
    """
    Функция экспорта текущего справочника в Excel
    Автор: Бохан Д.В.
    Вход: отсутствует
    Выход: отсутствует
    """
    name = state["current_edit_df"]
    if not name or state["edit_tree"] is None:
        messagebox.showwarning("Ошибка", "Выберите справочник для экспорта.")
        return
    df = state["dfs"][name]
    p = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')])
    if p:
        df.to_excel(p, index=False)
        messagebox.showinfo("Экспорт", "Экспорт завершён")

def build_settings_tab(tab, root):
    """
    Функция построения вкладки настроек интерфейса
    Автор: Бохан Д.В.
    Вход: tab, root
    Выход: отсутствует
    """
    color_options = [
        ("Светлый серый", "#f0f0f0"),
        ("Белый", "#ffffff"),
        ("Бежевый", "#f5e9da"),
        ("Голубой", "#e0f7fa"),
        ("Салатовый", "#e6f9e6"),
        ("Розовый", "#fde0ef"),
        ("Тёмно-синий", "#2b3556"),
    ]
    color_names = [n for n, c in color_options]
    color_map = {n: c for n, c in color_options}
    tk.Label(tab, text="Цвет фона интерфейса:").pack(anchor='w', padx=12, pady=(10,2))
    bg_color_name_var = tk.StringVar(value=color_names[0])
    ttk.Combobox(tab, textvariable=bg_color_name_var, values=color_names, state='readonly').pack(fill='x', padx=12, pady=2)
    tk.Label(tab, text="Цвет кнопок:").pack(anchor='w', padx=12, pady=(10,2))
    btn_color_name_var = tk.StringVar(value=color_names[3])
    ttk.Combobox(tab, textvariable=btn_color_name_var, values=color_names, state='readonly').pack(fill='x', padx=12, pady=2)
    tk.Label(tab, text="Шрифт:").pack(anchor='w', padx=12, pady=(10,2))
    font_var = tk.StringVar(value='Arial')
    ttk.Combobox(tab, textvariable=font_var, values=['Times New Roman', 'Arial', 'Georgian'], state='readonly').pack(fill='x', padx=12, pady=2)
    tk.Label(tab, text="Размер шрифта:").pack(anchor='w', padx=12, pady=(10,2))
    font_size_var = tk.IntVar(value=10)
    tk.Spinbox(tab, from_=8, to=32, textvariable=font_size_var).pack(fill='x', padx=12, pady=2)
    def apply_settings():
        """
        Функция применения выбранных настроек интерфейса
        Автор: Бохан Д.В.
        Вход: отсутствует
        Выход: отсутствует
        """
        bg = color_map[bg_color_name_var.get()]
        btn = color_map[btn_color_name_var.get()]
        font = font_var.get()
        size = font_size_var.get()
        try:
            root.configure(bg=bg)
            style = ttk.Style(root)
            style.configure('TButton', background=btn, foreground='white', padding=6, font=(font, int(size)))
            style.configure('Treeview', rowheight=25, font=(font, int(size)))
            style.configure('TLabel', font=(font, int(size)))
            messagebox.showinfo("Настройки", "Настройки применены.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка применения настроек: {e}")
    tk.Button(tab, text="Применить", command=apply_settings).pack(pady=12)

if __name__ == '__main__':
    main()
