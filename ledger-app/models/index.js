const sequelize = require('../config/database');
const Word = require('./word');
const WordResiteRecord = require('./word_resite_record');
const AnswerList = require('./answer_list');
const WordTag = require('./word_tag');
const UserReviewProgress = require('./user_review_progress');

// 定义关联关系
Word.hasMany(WordResiteRecord, { foreignKey: 'word_id' });
WordResiteRecord.belongsTo(Word, { foreignKey: 'word_id' });
Word.belongsTo(WordTag, { foreignKey: 'tag_id' });
WordTag.hasMany(Word, { foreignKey: 'tag_id' });

module.exports = {
  sequelize,
  Word,
  WordResiteRecord,
  AnswerList,
  WordTag,
  UserReviewProgress
};