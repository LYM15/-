// 艾宾浩斯记忆曲线时间间隔（单位：小时）
const REVIEW_INTERVALS = {
  LEVEL_0: 5 / 60, // 5分钟
  LEVEL_1: 24,
  LEVEL_2: 24,
  LEVEL_3: 48,
  LEVEL_4: 48,
  LEVEL_5: 72,
  LEVEL_6: 192,
  LEVEL_7_PLUS: 365 * 24
};

// 题目类型常量
const QUESTION_TYPES = {
  CHOOSE_CN: 1,
  CHOOSE_EN: 2,
  PRONOUNCE_CHOOSE: 3,
  FILL_IN_BLANK: 4
};

// 最大复习等级
const MAX_RISITE_LEVEL = 7;

module.exports = {
  REVIEW_INTERVALS,
  QUESTION_TYPES,
  MAX_RISITE_LEVEL
};