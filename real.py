# -*- coding: utf-8 -*-

from kivymd.uix.textfield import MDTextField
from arabic_reshaper import reshape
from bidi.algorithm import get_display


class ArabicTextField(MDTextField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.real_text = ""

    def insert_text(self, substring, from_undo=False):

        # إضافة الحرف للنص الحقيقي
        self.real_text += substring

        # تشكيل النص العربي
        shaped = reshape(self.real_text)

        # تصحيح الاتجاه
        bidi_text = get_display(shaped)

        # تحديث النص
        self.text = bidi_text

        # وضع المؤشر في النهاية
        self.cursor = (len(self.text), 0)

    def do_backspace(self, from_undo=False, mode="bkspc"):

        # حذف حرف من النص الحقيقي
        self.real_text = self.real_text[:-1]

        shaped = reshape(self.real_text)
        bidi_text = get_display(shaped)

        self.text = bidi_text
        self.cursor = (len(self.text), 0)