const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const UserReviewProgress = sequelize.define('UserReviewProgress', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  user_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  pending_count: {
    type: DataTypes.INTEGER,
    defaultValue: 0
  },
  reviewed_count: {
    type: DataTypes.INTEGER,
    defaultValue: 0
  },
  last_update_time: {
    type: DataTypes.DATE,
    allowNull: false
  }
}, {
  tableName: 'user_review_progress'
});

module.exports = UserReviewProgress;