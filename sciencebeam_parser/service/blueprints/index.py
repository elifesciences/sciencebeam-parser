from flask import Blueprint


class IndexBlueprint(Blueprint):
    def __init__(self):
        super().__init__('index', __name__)
        self.route('/')(self.index)

    def index(self):
        return "ScienceBeam Parser"
