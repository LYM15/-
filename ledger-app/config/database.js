const { Sequelize } = require('sequelize');

const sequelize = new Sequelize({
  dialect: 'mysql',
  host: 'localhost',
  port: 3306,
  username: 'root',
  password: 'password',
  database: 'eng_learning_ai',
  logging: console.log,
  define: {
    timestamps: true,
    underscored: true
  }
});

module.exports = sequelize;