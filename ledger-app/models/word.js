const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Word = sequelize.define('Word', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  word_name: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  explains: {
    type: DataTypes.STRING(500),
    allowNull: false
  },
  pronounce_us: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  tag_id: {
    type: DataTypes.INTEGER,
    allowNull: true
  }
}, {
  tableName: 'words'
});

module.exports = Word;