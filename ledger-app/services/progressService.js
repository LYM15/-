const { UserReviewProgress, WordResiteRecord } = require('../models');
const { Op } = require('sequelize');

/**
 * 初始化或更新用户复习进度
 * @param {number} userId - 用户ID
 * @returns {Promise<Object>} 复习进度对象
 */
async function initProgress(userId) {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
  
  // 查找用户的复习进度记录
  let progress = await UserReviewProgress.findOne({
    where: { user_id: userId }
  });
  
  // 如果记录不存在或需要更新
  if (!progress || progress.last_update_time < todayStart) {
    // 计算待复习单词数
    const pendingCount = await WordResiteRecord.count({
      where: {
        user_id: userId,
        next_review_time: {
          [Op.lt]: now
        }
      }
    });
    
    if (progress) {
      // 更新现有记录
      await progress.update({
        pending_count: pendingCount,
        reviewed_count: 0, // 每天重置已复习数
        last_update_time: now
      });
    } else {
      // 创建新记录
      progress = await UserReviewProgress.create({
        user_id: userId,
        pending_count: pendingCount,
        reviewed_count: 0,
        last_update_time: now
      });
    }
  }
  
  return progress;
}

/**
 * 获取今天需要的复习单词数和已复习单词数
 * @param {number} userId - 用户ID
 * @returns {Promise<Object>} 复习进度信息
 */
async function getTodayReviewCount(userId) {
  // 初始化或更新复习进度
  const progress = await initProgress(userId);
  
  return {
    pendingCount: progress.pending_count,
    reviewedCount: progress.reviewed_count
  };
}

/**
 * 更新复习进度
 * @param {number} userId - 用户ID
 * @param {boolean} isComplete - 是否完成复习
 * @returns {Promise<void>}
 */
async function updateProgress(userId, isComplete) {
  // 初始化或更新复习进度
  const progress = await initProgress(userId);
  
  // 更新进度
  if (isComplete) {
    await progress.update({
      pending_count: Math.max(0, progress.pending_count - 1),
      reviewed_count: progress.reviewed_count + 1
    });
  }
}

module.exports = {
  getTodayReviewCount,
  updateProgress
};