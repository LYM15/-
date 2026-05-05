const { Word, WordResiteRecord, AnswerList, sequelize } = require('../models');
const { Op } = require('sequelize');

// 常量定义
const QUESTION_TYPES = {
  CHOOSE_CN: 'CHOOSE_CN',
  CHOOSE_EN: 'CHOOSE_EN',
  PRONOUNCE_CHOOSE: 'PRONOUNCE_CHOOSE',
  FILL_IN_BLANK: 'FILL_IN_BLANK'
};

/**
 * 获取待复习的单词记录
 * @param {number} userId - 用户ID
 * @returns {Promise<Array>} 待复习的单词记录列表
 */
async function getPendingWords(userId) {
  const now = new Date();
  return await WordResiteRecord.findAll({
    where: {
      user_id: userId,
      next_review_time: {
        [Op.lt]: now
      }
    },
    include: [{ model: Word }]
  });
}

/**
 * 获取随机选项
 * @param {number} userId - 用户ID
 * @param {number} wordId - 单词ID
 * @param {string} type - 题目类型
 * @returns {Promise<Array>} 随机选项列表
 */
async function getRandomOptions(userId, wordId, type) {
  // 获取用户的最大 order_id
  const maxOrderIdRecord = await AnswerList.findOne({
    where: { user_id: userId },
    order: [['order_id', 'DESC']]
  });
  
  if (!maxOrderIdRecord) {
    return [];
  }
  
  const maxOrderId = maxOrderIdRecord.order_id;
  const randomOrderIds = [];
  
  // 生成3个随机 order_id
  while (randomOrderIds.length < 3) {
    const randomId = Math.floor(Math.random() * maxOrderId) + 1;
    if (!randomOrderIds.includes(randomId)) {
      randomOrderIds.push(randomId);
    }
  }
  
  // 获取当前 word_id 对应的 order_id
  const wordAnswerRecord = await AnswerList.findOne({
    where: { user_id: userId, word_name: (await Word.findByPk(wordId)).word_name }
  });
  
  if (wordAnswerRecord) {
    // 随机插入到 1-4 的位置
    const insertPosition = Math.floor(Math.random() * 4);
    randomOrderIds.splice(insertPosition, 0, wordAnswerRecord.order_id);
  }
  
  // 查询对应的选项
  const options = await AnswerList.findAll({
    where: {
      user_id: userId,
      order_id: randomOrderIds
    }
  });
  
  return options;
}

/**
 * 生成选择题
 * @param {Object} word - 单词对象
 * @param {number} userId - 用户ID
 * @param {string} type - 题目类型
 * @returns {Promise<Object>} 题目对象
 */
async function generateChooseQuestion(word, userId, type) {
  const options = await getRandomOptions(userId, word.id, type);
  let question = {
    id: word.id,
    type: type,
    options: []
  };
  
  switch (type) {
    case QUESTION_TYPES.CHOOSE_CN:
      question.question = word.word_name;
      options.forEach(option => {
        question.options.push({
          id: option.id,
          text: option.description
        });
      });
      break;
    case QUESTION_TYPES.CHOOSE_EN:
      question.question = word.explains;
      options.forEach(option => {
        question.options.push({
          id: option.id,
          text: option.word_name
        });
      });
      break;
    case QUESTION_TYPES.PRONOUNCE_CHOOSE:
      question.question = word.pronounce_us;
      options.forEach(option => {
        question.options.push({
          id: option.id,
          text: option.description
        });
      });
      break;
    case QUESTION_TYPES.FILL_IN_BLANK:
      question.question = word.explains;
      question.show_info = generateFillInBlank(word.word_name);
      break;
  }
  
  return question;
}

/**
 * 生成填空题的挖空效果
 * @param {string} wordName - 单词名称
 * @returns {Array} 挖空后的字符数组，空用 _ 表示
 */
function generateFillInBlank(wordName) {
  const chars = wordName.split('');
  const length = chars.length;
  const keepCount = Math.max(1, Math.floor(length / 5)); // 至少保留1个字母
  const keepIndices = new Set();
  
  // 随机选择要保留的索引
  while (keepIndices.size < keepCount) {
    const randomIndex = Math.floor(Math.random() * length);
    keepIndices.add(randomIndex);
  }
  
  // 生成挖空后的数组
  return chars.map((char, index) => {
    return keepIndices.has(index) ? char : '_';
  });
}

/**
 * 获取待背单词及其复习题目
 * @param {number} userId - 用户ID
 * @returns {Promise<Array>} 待背单词及其复习题目列表
 */
const { MAX_RISITE_LEVEL } = require('../constants/global');

async function getPendingWordsWithQuestions(userId) {
  const pendingWords = await getPendingWords(userId);
  const result = [];
  
  for (const record of pendingWords) {
    const word = record.Word;
    const questions = [];
    
    // 生成四种类型的题目
    questions.push(await generateChooseQuestion(word, userId, QUESTION_TYPES.CHOOSE_CN));
    questions.push(await generateChooseQuestion(word, userId, QUESTION_TYPES.CHOOSE_EN));
    questions.push(await generateChooseQuestion(word, userId, QUESTION_TYPES.PRONOUNCE_CHOOSE));
    questions.push(await generateChooseQuestion(word, userId, QUESTION_TYPES.FILL_IN_BLANK));
    
    // 添加 tag_id 和复习进度信息
    const wordWithProgress = {
      ...word.toJSON(),
      tag_id: word.tag_id || null,
      level: record.level || 0,
      max_level: MAX_RISITE_LEVEL
    };
    
    result.push({
      word: wordWithProgress,
      questions: questions
    });
  }
  
  return result;
}

module.exports = {
  getPendingWordsWithQuestions,
  QUESTION_TYPES
};