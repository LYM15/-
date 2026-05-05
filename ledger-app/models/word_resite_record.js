const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const WordResiteRecord = sequelize.define('WordResiteRecord', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  user_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  word_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  next_review_time: {
    type: DataTypes.DATE,
    allowNull: false
  },
  total_correct: {
    type: DataTypes.INTEGER,
    defaultValue: 0
  },
  total_wrong: {
    type: DataTypes.INTEGER,
    defaultValue: 0
  },
  score: {
    type: DataTypes.INTEGER,
    defaultValue: 0
  },
  level: {
    type: DataTypes.INTEGER,
    defaultValue: 0
  }
}, {
  tableName: 'words_resite_record'
});

module.exports = WordResiteRecord;