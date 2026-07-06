"""五笔编码引擎基础单元测试"""

import unittest
import sys
import os

# 确保能导入 wubi_ime 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from wubi_ime.engine import WubiEngine, Action


class TestWubiEngine(unittest.TestCase):
    """测试 WubiEngine 核心行为"""

    def test_add_key(self):
        """输入编码字母应追加到当前编码"""
        engine = WubiEngine()
        result = engine.process_key('w')
        self.assertEqual(result, (Action.ADD_KEY, None))
        self.assertEqual(engine.current_code, 'w')

    def test_select_candidate_by_digit(self):
        """数字键应返回选择候选字动作；由调用方执行 select_candidate 清空状态"""
        engine = WubiEngine()
        engine.process_key('w')  # 人
        result = engine.process_key('1')
        self.assertEqual(result, (Action.SELECT_CANDIDATE, '0'))
        # process_key 不直接修改状态，调用 select_candidate 才会清空
        candidate = engine.select_candidate(0)
        self.assertIsNotNone(candidate)
        self.assertEqual(engine.current_code, '')

    def test_space_submits_first_candidate(self):
        """空格应提交第一个候选字并清空编码"""
        engine = WubiEngine()
        engine.process_key('w')  # 人
        candidates = engine.current_candidates
        self.assertTrue(candidates)
        result = engine.process_key(' ')
        self.assertEqual(result, (Action.SUBMIT, candidates[0]))
        self.assertEqual(engine.current_code, '')

    def test_backspace_deletes_code(self):
        """退格应删除最后一个编码字符"""
        engine = WubiEngine()
        engine.process_key('w')
        engine.process_key('w')
        self.assertEqual(engine.current_code, 'ww')
        result = engine.process_key('backspace')
        self.assertEqual(result, (Action.DELETE, None))
        self.assertEqual(engine.current_code, 'w')

    def test_esc_clears_code(self):
        """Esc 应取消输入"""
        engine = WubiEngine()
        engine.process_key('w')
        result = engine.process_key('esc')
        self.assertEqual(result, (Action.CANCEL, None))
        self.assertEqual(engine.current_code, '')

    def test_shift_toggles_mode(self):
        """Shift 应返回切换模式动作；由调用方执行 toggle_mode 切换状态"""
        engine = WubiEngine()
        self.assertTrue(engine.is_chinese_mode())
        result = engine.process_key('shift')
        self.assertEqual(result, (Action.SWITCH_MODE, None))
        # process_key 不直接修改状态，调用 toggle_mode 才会切换
        engine.toggle_mode()
        self.assertFalse(engine.is_chinese_mode())

    def test_four_code_auto_submit(self):
        """四码唯一精确匹配应自动上屏"""
        engine = WubiEngine()
        # hhhh 在编码表中为唯一精确匹配
        for key in 'hhhh':
            result = engine.process_key(key)
        self.assertEqual(result[0], Action.SUBMIT)
        self.assertEqual(engine.current_code, '')

    def test_select_candidate_clears_state(self):
        """选择候选字后引擎状态应清空"""
        engine = WubiEngine()
        engine.process_key('w')
        candidate = engine.select_candidate(0)
        self.assertIsNotNone(candidate)
        self.assertEqual(engine.current_code, '')
        self.assertEqual(engine.current_candidates, [])


if __name__ == '__main__':
    unittest.main()
