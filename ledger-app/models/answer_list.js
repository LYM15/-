const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const AnswerList = sequelize.define('AnswerList', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  user_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  order_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  word_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  word_name: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  description: {
    type: DataTypes.STRING(500),
    allowNull: false
  }
}, {
  tableName: 'answer_list'
});

module.exports = AnswerList;