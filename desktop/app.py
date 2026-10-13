"""Interface de consulta em Tkinter para Windows e Linux."""

import argparse
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import font, ttk

from client import ApiError, search


STATES = ('', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT',
          'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR',
          'SC', 'SP', 'SE', 'TO')
BLUE, BACKGROUND, INK = '#0C326F', '#F7FAFC', '#464646'


class ConsultaApp(tk.Tk):
    def __init__(self, api_url='http://localhost:8000'):
        super().__init__()
        self.title('Consulta de servidores públicos')
        self.geometry(f'1100x{min(760, self.winfo_screenheight() - 100)}')
        self.minsize(900, 620)
        self.configure(background=BACKGROUND)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.api_url = tk.StringVar(value=api_url)
        self.fields = {key: tk.StringVar(value='') for key in ('nome', 'cargo', 'uf', 'orgao')}
        self.mode = tk.StringVar(value='Exata')
        self.limit = tk.StringVar(value='100')
        self.status = tk.StringVar(value='Preencha um ou mais filtros para começar.')
        self.page_label = tk.StringVar(value='Nenhuma consulta realizada')
        self.loading = False
        self.page, self.pages = 1, 0
        self.last_filters, self.last_api = {}, ''
        self.results = Queue()
        self.inputs = []
        self._styles()
        self._layout()
        self.bind('<Return>', lambda event: self.submit())
        self.poll_id = self.after(60, self._poll)
        self.name_entry.focus_set()

    def _styles(self):
        font.nametofont('TkDefaultFont').configure(size=10)
        font.nametofont('TkTextFont').configure(size=10)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background=BACKGROUND)
        style.configure('TLabel', background=BACKGROUND, foreground=INK)
        style.configure('Title.TLabel', font=('TkDefaultFont', 19, 'bold'), foreground='white', background=BLUE)
        style.configure('Section.TLabel', font=('TkDefaultFont', 12, 'bold'), foreground=BLUE)
        style.configure('TButton', padding=(14, 7))
        style.configure('Search.TButton', background=BLUE, foreground='white')
        style.map('Search.TButton', background=[('disabled', '#D5DCE5'), ('active', '#1351B4')],
                  foreground=[('disabled', '#464646')])
        style.configure('TEntry', padding=5)
        style.configure('TCombobox', padding=5)
        style.configure('Treeview', font=('TkDefaultFont', 10), rowheight=30, background='white', fieldbackground='white')
        style.configure('Treeview.Heading', font=('TkDefaultFont', 10, 'bold'), foreground=BLUE, padding=7)
        style.map('Treeview', background=[('selected', BLUE)], foreground=[('selected', 'white')])

    def _layout(self):
        header = tk.Frame(self, background=BLUE)
        header.grid(row=0, column=0, sticky='ew')
        ttk.Label(header, text='Consulta de servidores públicos', style='Title.TLabel').pack(anchor='w', padx=24, pady=15)
        tk.Frame(header, height=3, background='#ECDA3C').pack(fill='x')

        connection = ttk.Frame(self, padding=(24, 12, 24, 4))
        connection.grid(row=1, column=0, sticky='ew')
        connection.columnconfigure(1, weight=1)
        ttk.Label(connection, text='Endereço da API').grid(row=0, column=0, padx=(0, 12))
        api_entry = ttk.Entry(connection, textvariable=self.api_url)
        api_entry.grid(row=0, column=1, sticky='ew')
        self.inputs.append((api_entry, 'normal'))

        form = ttk.Frame(self, padding=(24, 8))
        form.grid(row=2, column=0, sticky='ew')
        for column in (0, 1, 2):
            form.columnconfigure(column, weight=1, uniform='filters')
        self.name_entry = self._field(form, 'Nome', self.fields['nome'], 0, 0)
        self._field(form, 'Tipo de busca por nome', self.mode, 0, 1, ('Exata', 'Similaridade'))
        self._field(form, 'Limite da similaridade (1 a 100)', self.limit, 0, 2)
        self._field(form, 'Cargo', self.fields['cargo'], 1, 0)
        self._field(form, 'UF (vazio: todas)', self.fields['uf'], 1, 1, STATES)
        self._field(form, 'Órgão', self.fields['orgao'], 1, 2)
        ttk.Label(form, text='Na similaridade, % separa trechos do nome: %NOME%SOBRENOME%.').grid(
            row=4, column=0, columnspan=3, sticky='w', pady=(7, 3))
        actions = ttk.Frame(form)
        actions.grid(row=5, column=0, columnspan=3, sticky='e', pady=(5, 0))
        self.clear_button = ttk.Button(actions, text='Limpar filtros', command=self.clear)
        self.clear_button.pack(side='left', padx=(0, 8))
        self.search_button = ttk.Button(actions, text='Buscar servidores', style='Search.TButton', command=self.submit)
        self.search_button.pack(side='left')

        result = ttk.Frame(self, padding=(24, 4, 24, 0))
        result.grid(row=3, column=0, sticky='nsew')
        result.columnconfigure(0, weight=1)
        result.rowconfigure(2, weight=1)
        ttk.Label(result, text='Resultados', style='Section.TLabel').grid(row=0, column=0, sticky='w')
        self.status_widget = ttk.Label(result, textvariable=self.status, wraplength=1020)
        self.status_widget.grid(row=1, column=0, sticky='ew', pady=(5, 8))
        self.bind('<Configure>', self._wrap_status)
        columns = ('nome', 'cargo', 'uf', 'orgao')
        self.table = ttk.Treeview(result, columns=columns, show='headings', selectmode='browse', height=5)
        for key, title, width in zip(columns, ('Nome', 'Cargo', 'UF', 'Órgão'), (290, 260, 105, 310)):
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=85 if key == 'uf' else 130, stretch=key != 'uf')
        self.table.grid(row=2, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(result, orient='vertical', command=self.table.yview)
        vertical.grid(row=2, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(result, orient='horizontal', command=self.table.xview)
        horizontal.grid(row=3, column=0, sticky='ew')
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.bind('<<TreeviewSelect>>', self._select_row)

        footer = ttk.Frame(self, padding=(24, 10))
        footer.grid(row=4, column=0, sticky='ew')
        footer.columnconfigure(1, weight=1)
        self.previous_button = ttk.Button(footer, text='Anterior', state='disabled', command=lambda: self.load_page(self.page - 1))
        self.previous_button.grid(row=0, column=0)
        ttk.Label(footer, textvariable=self.page_label, anchor='center').grid(row=0, column=1, sticky='ew')
        self.next_button = ttk.Button(footer, text='Próxima', state='disabled', command=lambda: self.load_page(self.page + 1))
        self.next_button.grid(row=0, column=2)
        self.details = tk.Text(footer, height=4, wrap='word', relief='flat', background=BACKGROUND,
                               foreground=INK, font='TkDefaultFont', state='disabled', takefocus=True)
        self.details.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(8, 0))
        self._details('Selecione um resultado para ler os campos completos. O texto pode ser copiado.')

    def _field(self, parent, label, variable, row, column, values=None):
        padx = (0 if column == 0 else 8, 0 if column == 2 else 8)
        ttk.Label(parent, text=label).grid(row=row * 2, column=column, sticky='w', padx=padx, pady=(3, 2))
        widget = (ttk.Combobox(parent, textvariable=variable, values=values, state='readonly')
                  if values is not None else ttk.Entry(parent, textvariable=variable))
        widget.grid(row=row * 2 + 1, column=column, sticky='ew', padx=padx, pady=(0, 3))
        self.inputs.append((widget, 'readonly' if values is not None else 'normal'))
        return widget

    def _wrap_status(self, event):
        if event.widget is self:
            self.status_widget.configure(wraplength=max(300, event.width - 60))

    def submit(self):
        # Busca nova usa o formulário; a paginação guarda uma cópia desses filtros.
        if self.loading:
            return
        filters = {key: value.get().strip() for key, value in self.fields.items()}
        if self.mode.get() == 'Similaridade' and filters['nome']:
            filters['similar'] = filters.pop('nome')
            filters['limit'] = self.limit.get().strip() or '100'
        if not any(filters.get(key) for key in ('nome', 'similar', 'cargo', 'uf', 'orgao')):
            self._empty()
            self.status.set('Preencha pelo menos um filtro para buscar.')
            return
        self.last_filters, self.last_api = filters, self.api_url.get()
        self._empty()
        self.load_page(1)

    def load_page(self, page):
        if self.loading or page < 1:
            return
        self._busy(True)
        self.status.set('Consultando a API…')
        # A rede fica fora da thread do Tk. Só a fila é compartilhada.
        def fetch():
            try:
                outcome = search(self.last_api, self.last_filters, page)
            except ApiError as error:
                outcome = error
            except Exception:
                outcome = ApiError('Não foi possível ler a consulta. Tente novamente.')
            self.results.put(outcome)
        Thread(target=fetch, daemon=True).start()

    def _poll(self):
        # after roda na thread do Tk: é aqui, e não na thread de rede, que a tela muda.
        try:
            outcome = self.results.get_nowait()
        except Empty:
            pass
        else:
            if isinstance(outcome, ApiError):
                self.status.set(str(outcome))
            else:
                self._empty()
                for row in outcome['dados']:
                    self.table.insert('', 'end', values=(row['nome'], row['cargo'], row['uf'] or 'Não informada', row['orgao']))
                pagination = outcome['paginacao']
                self.page, self.pages = pagination['pagina'], pagination['total_paginas']
                total = pagination['total_registros']
                self.status.set('Nenhum servidor encontrado. Revise os filtros.' if total == 0 else
                                f'{total} servidor(es) encontrado(s). Selecione uma linha para ver os detalhes.')
                self.page_label.set(f'Página {self.page} de {self.pages}' if total else 'Sem resultados')
            self._busy(False)
        self.poll_id = self.after(60, self._poll)

    def destroy(self):
        # Não deixa o callback agendado tentar acessar widgets já destruídos.
        self.after_cancel(self.poll_id)
        super().destroy()

    def _busy(self, busy):
        self.loading = busy
        for widget, normal_state in self.inputs:
            widget.configure(state='disabled' if busy else normal_state)
        self.search_button.configure(state='disabled' if busy else 'normal')
        self.clear_button.configure(state='disabled' if busy else 'normal')
        self.previous_button.configure(state='normal' if not busy and self.page > 1 else 'disabled')
        self.next_button.configure(state='normal' if not busy and self.page < self.pages else 'disabled')

    def _empty(self):
        self.table.delete(*self.table.get_children())
        self.page, self.pages = 1, 0
        self.page_label.set('Nenhuma consulta realizada')
        self.previous_button.configure(state='disabled')
        self.next_button.configure(state='disabled')
        self._details('Selecione um resultado para ler os campos completos. O texto pode ser copiado.')

    def clear(self):
        if self.loading:
            return
        for value in self.fields.values():
            value.set('')
        self.mode.set('Exata')
        self.limit.set('100')
        self._empty()
        self.status.set('Preencha um ou mais filtros para começar.')
        self.name_entry.focus_set()

    def _details(self, text):
        self.details.configure(state='normal')
        self.details.delete('1.0', 'end')
        self.details.insert('1.0', text)
        self.details.configure(state='disabled')

    def _select_row(self, event=None):
        # As colunas podem cortar textos longos; os detalhes mostram o valor completo.
        selected = self.table.selection()
        if selected:
            values = self.table.item(selected[0], 'values')
            self._details('\n'.join(f'{label}: {value}' for label, value in zip(('Nome', 'Cargo', 'UF', 'Órgão'), values)))


def main():
    parser = argparse.ArgumentParser(description='Consulta de servidores públicos via API HTTP.')
    parser.add_argument('--api-url', default='http://localhost:8000', help='Endereço da API Flask')
    args = parser.parse_args()
    ConsultaApp(args.api_url).mainloop()


if __name__ == '__main__':
    main()
