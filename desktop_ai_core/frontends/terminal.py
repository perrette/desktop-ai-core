class Item:
    def __init__(self, name, callback, checked=None, checkable=False, visible=True, help=""):
        self.name = name
        self._callback = callback
        self.checkable = checkable or (checked is not None)
        self.checked = (checked if callable(checked) else lambda item: checked)
        self.help = help
        self.visible = visible if callable(visible) else lambda item: visible

    def __call__(self, app, item):
        return self._callback(app, self)

    def __str__(self):
        return self.name

class SetValueItem(Item):
    def __init__(self, name, callback, value=None, choices=None, type=None, **kwargs):
        super().__init__(name, callback, **kwargs)
        self.value = value
        self.choices = choices
        self.type = type

    def _isvalid(self, value):

        if self.type:
            try:
                value = self.type(value)
            except ValueError as error:
                print(f"Invalid type: {str(error)}")
                return False

        if self.choices and value not in self.choices:
            print(f"Valid choices are {', '.join(map(str, self.choices))}. Got: {str(error)}")
            return False

        return True

    def __call__(self, app, item):
        self.is_active = True
        while self.is_active:
            value = self.value(item)
            ans = input(f"Enter value for {self.name} (current {value}): ")
            if not ans.strip():
                ans = value
            if self._isvalid(ans):
                self.value = lambda item: ans
                self.is_active = False
        return self._callback(app, item)

class Menu:
    def __init__(self, items, name=None, help=""):
        self.items = items
        self.name = name
        self.help = help
        self.choices = {}
        self.is_active_menu = False

    def __call__(self, app, _):
        self.is_active_menu = True
        while app.is_running and self.is_active_menu:
            self.show(app)
            self.prompt(app)

    def show(self, app):
        print(f"\n{self.name or 'Options:'}")

        count = 0
        for item in self.items:
            if not item.visible(item):
                continue
            count += 1
            ticked = " "
            if item.checkable and item.checked(item):
                ticked = "✓"
            if hasattr(item, "value") and item.value(item):
                suffix = f"({item.value(item)})"
            else:
                suffix = ""
            print(f"{ticked} {count}. {item.help or item.name} {suffix}")
            self.choices[str(count)] = item
            self.choices[item.name] = item

    def prompt(self, app, title=None):

        if getattr(app, "_player", None):
            app.update_progress(app._player)

        choice = input("\nChoose an option: ")

        if choice in self.choices:
            item = self.choices[choice]
            print(item)
            ans = item(app, item)
            if isinstance(ans, bool):
                self.is_active_menu = ans

        elif choice in ("quit", "q"):
            self.is_active_menu = False

        else:
            return print(f"Invalid choice: {choice}")
