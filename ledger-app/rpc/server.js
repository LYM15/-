const http = require('http');
const url = require('url');
const querystring = require('querystring');
const { submitAnswer } = require('../services/answerService');
const { getTodayReviewCount } = require('../services/progressService');

// 创建 HTTP 服务器
const server = http.createServer(async (req, res) => {
  // 解析请求 URL
  const parsedUrl = url.parse(req.url);
  const pathname = parsedUrl.pathname;
  
  // 处理提交答案的请求
  if (pathname === '/submitAnswer') {
    let body = '';
    
    // 读取请求体
    req.on('data', chunk => {
      body += chunk;
    });
    
    // 处理请求完成
    req.on('end', async () => {
      try {
        // 解析请求参数
        const params = querystring.parse(body);
        const userId = parseInt(params.userId);
        const wordId = parseInt(params.wordId);
        const answerId = parseInt(params.answerId);
        const questionType = parseInt(params.questionType);
        const filledName = params.filled_name;
        
        // 验证参数
        if (isNaN(userId) || isNaN(wordId) || isNaN(questionType)) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: false, message: '参数错误' }));
          return;
        }
        
        // 调用提交答案的函数
        const result = await submitAnswer(userId, wordId, answerId, questionType, filledName);
        
        // 返回结果
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (error) {
        console.error('处理请求失败:', error);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, message: '服务器内部错误' }));
      }
    });
  } else if (pathname === '/getTodayReviewCount') {
    // 处理获取今日复习单词数的请求
    try {
      // 解析查询参数
      const queryParams = url.parse(req.url, true).query;
      const userId = parseInt(queryParams.userId);
      
      // 验证参数
      if (isNaN(userId)) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, message: '参数错误' }));
        return;
      }
      
      // 调用获取今日复习单词数的函数
      const result = await getTodayReviewCount(userId);
      
      // 返回结果
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        pendingCount: result.pendingCount,
        reviewedCount: result.reviewedCount
      }));
    } catch (error) {
      console.error('处理请求失败:', error);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, message: '服务器内部错误' }));
    }
  } else {
    // 处理其他请求
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: false, message: '接口不存在' }));
  }
});

// 启动服务器
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`RPC 服务已启动，监听端口 ${PORT}`);
});

module.exports = server;