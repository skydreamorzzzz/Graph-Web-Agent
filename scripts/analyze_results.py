"""
Analyze Results - 分析实验结果
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class ResultAnalyzer:
    """结果分析器"""
    
    def __init__(self, results_dir: str = "results/performance"):
        self.results_dir = Path(results_dir)
        self.results = []
        
    def load_results(self, pattern: str = "*.json") -> None:
        """加载结果文件"""
        result_files = list(self.results_dir.glob(pattern))
        
        print(f"找到 {len(result_files)} 个结果文件")
        
        for filepath in result_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.results.append({
                    "filename": filepath.name,
                    "data": data
                })
    
    def compare_variants(self, variant_names: List[str] = None) -> None:
        """比较不同实验变体"""
        if not variant_names:
            variant_names = ["baseline", "graph_only", "graph_with_repair", "full_system"]
        
        # 提取各变体的指标
        metrics = {
            "success_rate": [],
            "avg_steps": [],
            "avg_llm_calls": [],
            "cost_per_success": []
        }
        
        for result in self.results:
            data = result["data"]
            metrics["success_rate"].append(data.get("success_rate", 0))
            metrics["avg_steps"].append(data.get("avg_steps", 0))
            metrics["avg_llm_calls"].append(data.get("avg_llm_calls", 0))
            metrics["cost_per_success"].append(data.get("cost_per_success", 0))
        
        # 绘制对比图
        self._plot_comparison(variant_names, metrics)
    
    def analyze_failures(self) -> None:
        """分析失败分布"""
        all_failures = {}
        
        for result in self.results:
            data = result["data"]
            failure_dist = data.get("failure_distribution", {})
            
            for failure_type, count in failure_dist.items():
                if failure_type not in all_failures:
                    all_failures[failure_type] = 0
                all_failures[failure_type] += count
        
        # 绘制失败分布饼图
        self._plot_failure_distribution(all_failures)
    
    def analyze_repair_depth(self) -> None:
        """分析修复深度分布"""
        all_repair_depths = []
        
        for result in self.results:
            data = result["data"]
            raw_metrics = data.get("raw_metrics", {})
            repair_depths = raw_metrics.get("repair_depths", [])
            all_repair_depths.extend(repair_depths)
        
        if all_repair_depths:
            self._plot_repair_depth_distribution(all_repair_depths)
    
    def generate_report(self, output_path: str = "results/analysis_report.txt") -> None:
        """生成分析报告"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("实验结果分析报告")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for i, result in enumerate(self.results, 1):
            filename = result["filename"]
            data = result["data"]
            
            report_lines.append(f"\n实验 {i}: {filename}")
            report_lines.append("-" * 80)
            report_lines.append(f"总任务数: {data.get('total_tasks', 0)}")
            report_lines.append(f"成功率: {data.get('success_rate', 0):.2%}")
            report_lines.append(f"平均步数: {data.get('avg_steps', 0):.1f}")
            report_lines.append(f"平均LLM调用: {data.get('avg_llm_calls', 0):.1f}")
            report_lines.append(f"每次成功成本: ${data.get('cost_per_success', 0):.4f}")
            report_lines.append(f"平均持续时间: {data.get('avg_duration', 0):.1f}秒")
            report_lines.append(f"平均修复深度: {data.get('avg_repair_depth', 0):.1f}")
            
            failure_dist = data.get('failure_distribution', {})
            if failure_dist:
                report_lines.append("\n失败分布:")
                for failure_type, count in failure_dist.items():
                    report_lines.append(f"  - {failure_type}: {count}")
        
        report_lines.append("\n" + "=" * 80)
        
        # 保存报告
        report_text = "\n".join(report_lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\n报告已保存到: {output_path}")
    
    def _plot_comparison(self, variant_names: List[str], metrics: Dict[str, List]) -> None:
        """绘制对比图"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('实验变体对比', fontsize=16)
        
        # 成功率
        axes[0, 0].bar(range(len(variant_names)), [m * 100 for m in metrics["success_rate"]])
        axes[0, 0].set_title('成功率 (%)')
        axes[0, 0].set_xticks(range(len(variant_names)))
        axes[0, 0].set_xticklabels(variant_names, rotation=45)
        
        # 平均步数
        axes[0, 1].bar(range(len(variant_names)), metrics["avg_steps"])
        axes[0, 1].set_title('平均步数')
        axes[0, 1].set_xticks(range(len(variant_names)))
        axes[0, 1].set_xticklabels(variant_names, rotation=45)
        
        # LLM调用次数
        axes[1, 0].bar(range(len(variant_names)), metrics["avg_llm_calls"])
        axes[1, 0].set_title('平均LLM调用次数')
        axes[1, 0].set_xticks(range(len(variant_names)))
        axes[1, 0].set_xticklabels(variant_names, rotation=45)
        
        # 成本
        axes[1, 1].bar(range(len(variant_names)), metrics["cost_per_success"])
        axes[1, 1].set_title('每次成功成本 ($)')
        axes[1, 1].set_xticks(range(len(variant_names)))
        axes[1, 1].set_xticklabels(variant_names, rotation=45)
        
        plt.tight_layout()
        plt.savefig('results/comparison.png', dpi=300, bbox_inches='tight')
        print("对比图已保存: results/comparison.png")
    
    def _plot_failure_distribution(self, failures: Dict[str, int]) -> None:
        """绘制失败分布饼图"""
        if not failures:
            return
        
        labels = list(failures.keys())
        sizes = list(failures.values())
        
        plt.figure(figsize=(10, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('失败类型分布')
        plt.axis('equal')
        
        plt.savefig('results/failure_distribution.png', dpi=300, bbox_inches='tight')
        print("失败分布图已保存: results/failure_distribution.png")
    
    def _plot_repair_depth_distribution(self, repair_depths: List[int]) -> None:
        """绘制修复深度分布"""
        plt.figure(figsize=(10, 6))
        plt.hist(repair_depths, bins=range(max(repair_depths) + 2), edgecolor='black')
        plt.title('修复深度分布')
        plt.xlabel('修复深度')
        plt.ylabel('频次')
        plt.grid(axis='y', alpha=0.3)
        
        plt.savefig('results/repair_depth_distribution.png', dpi=300, bbox_inches='tight')
        print("修复深度分布图已保存: results/repair_depth_distribution.png")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="分析实验结果")
    parser.add_argument("--results-dir", default="results/performance", help="结果目录")
    parser.add_argument("--pattern", default="*.json", help="文件匹配模式")
    
    args = parser.parse_args()
    
    analyzer = ResultAnalyzer(results_dir=args.results_dir)
    analyzer.load_results(pattern=args.pattern)
    
    if not analyzer.results:
        print("未找到结果文件")
        return
    
    # 生成报告
    analyzer.generate_report()
    
    # 分析失败
    analyzer.analyze_failures()
    
    # 分析修复深度
    analyzer.analyze_repair_depth()
    
    # 对比变体（如果有多个结果）
    if len(analyzer.results) > 1:
        analyzer.compare_variants()


if __name__ == "__main__":
    main()


