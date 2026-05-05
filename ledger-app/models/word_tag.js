const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const WordTag = sequelize.define('WordTag', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  tag_name: {
    type: DataTypes.STRING(50),
    allowNull: false
  },
  question_types: {
    type: DataTypes.INTEGER,
    allowNull: false
  }
}, {
  tableName: 'word_tags'
});

module.exports = WordTag;