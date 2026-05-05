const { WordResiteRecord, AnswerList } = require('../models');
const { Op } = require('sequelize');
const { REVIEW_INTERVALS, QUESTION_TYPES } = require('../constants/global');

/**
 * 提交答案
 * @param {number} userId - 用户ID
 * @param {number} wordId - 单词ID
 * @param {number} answerId - 答案ID
 * @param {number} questionType - 题目类型
 * @param {string} filledName - 填空题填写的单词
 * @returns {Promise<Object>} 提交结果
 */
async function submitAnswer(userId, wordId, answerId, questionType, filledName) {
  try {
    // 从 words_resite_record 表中获取对应记录
    const record = await WordResiteRecord.findOne({
      where: {
        user_id: userId,
        word_id: wordId
      }
    });
    
    // 检查记录是否存在
    if (!record) {
      return {
        success: false,
        message: '记录不存在'
      };
    }
    
    let isCorrect = false;
    
    // 根据题目类型验证答案
    if (questionType === QUESTION_TYPES.FILL_IN_BLANK) {
      // 填空题：从 words 表中获取单词信息，对比 filledName
      const word = await Word.findByPk(wordId);
      if (word) {
        isCorrect = filledName === word.word_name;
      }
    } else {
      // 其他题型：从 answer_list 表中获取对应记录
      const answerRecord = await AnswerList.findOne({
        where: {
          user_id: userId,
          id: answerId
        }
      });
      
      if (!answerRecord) {
        return {
          success: false,
          message: '记录不存在'
        };
      }
      
      // 校验答案是否正确
      isCorrect = answerRecord.word_id === wordId;
    }
    
    // 更新记录
    await updateRecord(record, isCorrect, questionType);
    
    return {
      success: true,
      isCorrect: isCorrect
    };
  } catch (error) {
    console.error('提交答案失败:', error);
    return {
      success: false,
      message: '提交答案失败'
    };
  }
}

/**
 * 更新单词复习记录
 * @param {Object} record - 单词复习记录
 * @param {boolean} isCorrect - 答案是否正确
 * @param {number} questionType - 题目类型
 * @returns {Promise<void>}
 */
async function updateRecord(record, isCorrect, questionType) {
  const now = new Date();
  let { total_correct, total_wrong, score, level } = record;
  const bitPosition = questionType - 1;
  
  if (isCorrect) {
    // 答案正确
    total_correct += 1;
    // 设置对应位为1
    score |= (1 << bitPosition);
    
    // 检查是否所有类型都正确（二进制 0、1、2、3 位都为 1，即 15）
    if (score === 15) {
      level += 1;
      // 根据 level 更新 next_review_time
      record.next_review_time = getNextReviewTime(level);
    }
  } else {
    // 答案错误
    total_wrong += 1;
    // 设置对应位为0
    score &= ~(1 << bitPosition);
    
    // 检查是否分数变为0且之前分数大于0
    if (score === 0 && record.score > 0) {
      level = Math.max(0, level - 1);
    }
    // 错误时，next_review_time 设为当前时间
    record.next_review_time = now;
  }
  
  // 更新记录
  await record.update({
    total_correct,
    total_wrong,
    score,
    level
  });
}

/**
 * 根据 level 计算下一次复习时间
 * @param {number} level - 当前级别
 * @returns {Date} 下一次复习时间
 */
function getNextReviewTime(level) {
  const now = new Date();
  let interval;
  
  switch (level) {
    case 0:
      interval = REVIEW_INTERVALS.LEVEL_0;
      break;
    case 1:
      interval = REVIEW_INTERVALS.LEVEL_1;
      break;
    case 2:
      interval = REVIEW_INTERVALS.LEVEL_2;
      break;
    case 3:
      interval = REVIEW_INTERVALS.LEVEL_3;
      break;
    case 4:
      interval = REVIEW_INTERVALS.LEVEL_4;
      break;
    case 5:
      interval = REVIEW_INTERVALS.LEVEL_5;
      break;
    case 6:
      interval = REVIEW_INTERVALS.LEVEL_6;
      break;
    default:
      interval = REVIEW_INTERVALS.LEVEL_7_PLUS;
  }
  
  const nextTime = new Date(now.getTime() + interval * 60 * 60 * 1000);
  return nextTime;
}

module.exports = {
  submitAnswer
};