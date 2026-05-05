const { sequelize } = require('./models');
const { getPendingWordsWithQuestions } = require('./services/reviewService');
const rpcServer = require('./rpc/server');

// 测试函数
async function testReviewService() {
  try {
    // 同步数据库模型
    await sequelize.sync({ force: true });
    console.log('数据库模型同步完成');
    
    // 测试获取待背单词
    const userId = 1;
    const pendingWords = await getPendingWordsWithQuestions(userId);
    console.log('待背单词数量:', pendingWords.length);
    
    // 输出每个单词及其题目
    pendingWords.forEach((item, index) => {
      console.log(`\n单词 ${index + 1}: ${item.word.word_name}`);
      item.questions.forEach((question, qIndex) => {
        console.log(`  题目 ${qIndex + 1} (${question.type}): ${question.question}`);
        question.options.forEach((option, oIndex) => {
          console.log(`    选项 ${oIndex + 1}: ${option.text}`);
        });
      });
    });
  } catch (error) {
    console.error('测试失败:', error);
  }
}

// 运行测试
testReviewService();

// 启动 RPC 服务
console.log('启动 RPC 服务...');