/**
 * 情感分析器 - 分析文本情感并映射到Live2D表情
 * 支持中文情感分析，可扩展
 */
class SentimentAnalyzer {
    constructor() {
        // 情感词典 - 可扩展
        this.emotionDict = {
            happy: {
                keywords: [
                    '高兴', '开心', '快乐', '欢喜', '幸福', '美好', '精彩', '壮观', '壮丽', '美丽',
                    '欢迎', '恭喜', '祝贺', '太好了', '不错', '很好', '棒', '赞', '喜欢', '爱',
                    '微笑', '笑', '乐', '欢', '喜', '吉祥', '如意', '祝福', '祈福', '许愿',
                    '金碧辉煌', '宏伟', '震撼', '绝美', '灿烂', '辉煌', '瑰丽', '典雅', '庄严',
                    '赞叹', '惊叹', '赏心悦目', '心旷神怡', '流连忘返', '叹为观止',
                    '灵验', '庇佑', '平安', '健康', '丰收', '圆满', '成功', '胜利',
                    '热闹', '喜庆', '庆祝', '盛宴', '盛典', '隆重', '盛况'
                ],
                weight: 1.0
            },
            surprised: {
                keywords: [
                    '惊讶', '意外', '没想到', '竟然', '居然', '天哪', '哇', '不可思议',
                    '难以置信', '震惊', '吃惊', '神奇', '奇迹', '罕见', '独特', '唯一',
                    '首次', '前所未有', '史无前例', '绝无仅有', '举世闻名', '世界之最'
                ],
                weight: 1.2
            },
            sad: {
                keywords: [
                    '遗憾', '可惜', '难过', '伤心', '悲伤', '不幸', '惋惜', '感叹', '沧桑',
                    '衰落', '消失', '失去', '离别', '思念', '忧愁', '哀', '悲', '痛',
                    '毁坏', '破坏', '战争', '灾难', '苦难', '坎坷', '曲折'
                ],
                weight: 1.1
            },
            angry: {
                keywords: [
                    '生气', '愤怒', '不满', '讨厌', '可恶', '岂有此理', '不可接受',
                    '禁止', '不准', '违规', '违法', '处罚', '惩罚'
                ],
                weight: 1.3
            },
            thinking: {
                keywords: [
                    '思考', '考虑', '想想', '分析', '研究', '探讨', '也许', '可能', '大概',
                    '据说', '传说', '相传', '据说', '猜测', '推测', '估计', '据说',
                    '历史', '由来', '起源', '故事', '典故', '记载', '文献'
                ],
                weight: 0.8
            },
            greeting: {
                keywords: [
                    '你好', '您好', '欢迎', '嗨', '早上好', '下午好', '晚上好',
                    '初次见面', '幸会', '久仰', '光临', '到来'
                ],
                weight: 1.5
            },
            explaining: {
                keywords: [
                    '因为', '所以', '因此', '由于', '原因', '结果', '导致', '使得',
                    '首先', '其次', '然后', '最后', '总之', '综上', '也就是说',
                    '具体来说', '详细', '包括', '分为', '组成', '结构'
                ],
                weight: 0.6
            }
        };

        // 否定词（会翻转情感）
        this.negationWords = ['不', '没', '无', '非', '未', '别', '莫', '勿', '休'];

        // 程度副词
        this.intensifiers = {
            '非常': 1.5, '特别': 1.5, '极其': 2.0, '十分': 1.5, '格外': 1.5,
            '相当': 1.3, '很': 1.2, '挺': 1.1, '比较': 0.8, '稍微': 0.6,
            '最': 2.0, '极': 2.0, '超': 1.5, '太': 1.8
        };
    }

    /**
     * 分析文本情感
     * @param {string} text - 输入文本
     * @returns {Object} 情感分析结果
     */
    analyze(text) {
        if (!text || text.trim().length === 0) {
            return { emotion: 'neutral', confidence: 0, scores: {} };
        }

        const scores = {};
        let totalScore = 0;

        // 计算每个情感类别的得分
        for (const [emotion, config] of Object.entries(this.emotionDict)) {
            let score = 0;

            for (const keyword of config.keywords) {
                const regex = new RegExp(keyword, 'g');
                const matches = text.match(regex);
                if (matches) {
                    // 基础分 = 关键词长度 * 匹配次数
                    let keywordScore = keyword.length * matches.length;

                    // 检查前面是否有程度副词
                    for (const [intensifier, multiplier] of Object.entries(this.intensifiers)) {
                        const intensifierRegex = new RegExp(intensifier + '.{0,3}' + keyword);
                        if (intensifierRegex.test(text)) {
                            keywordScore *= multiplier;
                        }
                    }

                    // 检查前面是否有否定词（简单处理）
                    for (const neg of this.negationWords) {
                        const negRegex = new RegExp(neg + '.{0,3}' + keyword);
                        if (negRegex.test(text)) {
                            keywordScore *= -0.5; // 否定翻转
                        }
                    }

                    score += keywordScore;
                }
            }

            scores[emotion] = score * config.weight;
            totalScore += Math.abs(scores[emotion]);
        }

        // 标点符号增强
        const exclamationCount = (text.match(/[！!]/g) || []).length;
        const questionCount = (text.match(/[？?]/g) || []).length;
        const ellipsisCount = (text.match(/[…。]{2,}|……/g) || []).length;

        if (exclamationCount > 0) {
            scores.happy = (scores.happy || 0) + exclamationCount * 2;
        }
        if (questionCount > 0) {
            scores.thinking = (scores.thinking || 0) + questionCount * 1.5;
        }
        if (ellipsisCount > 0) {
            scores.thinking = (scores.thinking || 0) + ellipsisCount * 1;
        }

        // 找到主导情感
        let maxScore = 0;
        let dominantEmotion = 'neutral';

        for (const [emotion, score] of Object.entries(scores)) {
            if (score > maxScore) {
                maxScore = score;
                dominantEmotion = emotion;
            }
        }

        // 置信度计算
        const confidence = totalScore > 0 ? maxScore / totalScore : 0;

        // 如果得分太低，默认为 explaining（解释说明）
        if (maxScore < 2) {
            dominantEmotion = 'explaining';
        }

        return {
            emotion: dominantEmotion,
            confidence: Math.min(1, confidence),
            scores: scores
        };
    }

    /**
     * 分析文本并返回表情序列（用于长文本分段表情）
     * @param {string} text - 输入文本
     * @returns {Array} 表情时间序列
     */
    analyzeWithTimeline(text) {
        const result = this.analyze(text);
        const timeline = [];

        // 按句子分割
        const sentences = text.split(/[。！？；\n]+/).filter(s => s.trim());

        if (sentences.length <= 1) {
            // 短文本，直接返回整体情感
            timeline.push({
                emotion: result.emotion,
                startDelay: 0,
                duration: 2500
            });
            return timeline;
        }

        // 长文本，每句分析
        let delay = 0;
        for (const sentence of sentences) {
            const sentenceResult = this.analyze(sentence);
            const duration = Math.max(1500, sentence.length * 150); // 每字约150ms

            timeline.push({
                emotion: sentenceResult.emotion,
                startDelay: delay,
                duration: duration
            });

            delay += duration;
        }

        return timeline;
    }

    /**
     * 获取情感对应的表情建议
     */
    getExpressionSuggestion(emotion) {
        const suggestions = {
            neutral: { expression: 'neutral', motion: null },
            happy: { expression: 'happy', motion: 'tap_body' },
            surprised: { expression: 'surprised', motion: null },
            sad: { expression: 'sad', motion: null },
            angry: { expression: 'angry', motion: 'shake' },
            thinking: { expression: 'thinking', motion: null },
            greeting: { expression: 'greeting', motion: 'tap_body' },
            explaining: { expression: 'explaining', motion: null }
        };

        return suggestions[emotion] || suggestions.neutral;
    }
}

// 全局单例
window.sentimentAnalyzer = new SentimentAnalyzer();
