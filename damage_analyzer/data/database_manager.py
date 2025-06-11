# database_manager.py - 数据库管理器
# 负责处理所有数据库相关操作，包括：
# - 数据库连接和初始化
# - 干员数据的增删改查
# - 计算记录的存储和检索
# - 数据导入导出功能
# - 统计与清理等辅助功能

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """简化的SQLite数据库管理器，封装了干员、计算、导入等多种数据库操作。"""
    
    def __init__(self, db_path: str = None):
        # 初始化数据库管理器，设置数据库路径并初始化表结构
        if db_path is None:
            # 在damage_analyzer项目根目录下创建SQLite数据库文件
            # 数据库文件将用于存储干员数据、计算记录和导入历史等信息
            analyzer_dir = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(analyzer_dir, 'damage_analyzer.db')
        
        self.db_path = db_path
        self.initialize_database()  # 初始化数据库表结构
    
    def get_connection(self):
        """获取数据库连接
        
        此方法用于创建并返回一个SQLite数据库连接对象。
        连接使用sqlite3.Row作为行工厂，使得可以通过列名访问查询结果。
        
        Returns:
            sqlite3.Connection: 配置好的数据库连接对象
            
        Note:
            - 连接会自动使用self.db_path指定的数据库文件
            - 返回的连接对象使用sqlite3.Row作为行工厂
            - 调用者负责在完成后关闭连接
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 查询结果可通过列名访问
        return conn
    
    def initialize_database(self):
        """初始化数据库表结构 - 修复版本
        
        此方法用于创建数据库表结构，包括干员信息、计算记录和导入记录等。
        修复时间存储使用本地时间而非UTC时间。
        
        Note:
            - 如果表已存在，则不会重复创建
            - 使用sqlite3.Row作为行工厂，使得可以通过列名访问查询结果
            - 修复时间戳默认值使用本地时间
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建干员信息表（使用本地时间）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                class_type TEXT NOT NULL,
                hp INTEGER,
                atk INTEGER,
                def INTEGER,
                mdef INTEGER,
                atk_speed REAL,
                atk_type TEXT,
                block_count INTEGER,
                cost INTEGER,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 创建计算记录表（使用本地时间）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER,
                calculation_type TEXT NOT NULL,
                parameters TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (operator_id) REFERENCES operators (id)
            )
        ''')
        
        # 创建导入记录表（使用本地时间）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_type TEXT NOT NULL,
                file_name TEXT,
                record_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 检查并添加缺失的列（兼容旧数据库）
        self._ensure_database_compatibility(cursor)
        
        conn.commit()
        conn.close()
    
    def _ensure_database_compatibility(self, cursor):
        """确保数据库兼容性，添加缺失的列"""
        try:
            # 检查operators表是否有updated_at列
            cursor.execute("PRAGMA table_info(operators)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'updated_at' not in columns:
                logger.info("添加operators.updated_at列...")
                cursor.execute('''
                    ALTER TABLE operators 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
                ''')
                
                # 为现有记录设置updated_at
                cursor.execute('''
                    UPDATE operators 
                    SET updated_at = datetime('now','localtime') 
                    WHERE updated_at IS NULL
                ''')
                
                logger.info("✅ updated_at列添加完成")
            
            # 修复现有记录的时间格式（将UTC时间转换为本地时间显示）
            # 注意：这里不修改已有数据，只是在查询时处理
            
        except Exception as e:
            logger.error(f"数据库兼容性检查失败: {e}")
    
    def test_connection(self) -> bool:
        """测试数据库连接
        
        此方法用于测试数据库连接是否正常。
        
        Returns:
            bool: 如果连接成功返回True，否则返回False
        """
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception:
            return False
    
    def insert_operator(self, operator_data: Dict[str, Any]) -> int:
        """插入干员数据 - 使用本地时间和智能ID分配
        
        此方法用于将干员数据插入到数据库中。
        会自动寻找最小可用的ID，实现删除后补位的功能。
        
        Args:
            operator_data: 包含干员信息的字典
        Returns:
            int: 新插入干员的ID
        Raises:
            Exception: 插入失败时抛出
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 处理可能的None值
            safe_data = {
                'name': operator_data.get('name', ''),
                'class_type': operator_data.get('class_type', '未知'),
                'hp': operator_data.get('hp', 0) or 0,
                'atk': operator_data.get('atk', 0) or 0,
                'def': operator_data.get('def', 0) or 0,
                'mdef': operator_data.get('mdef', 0) or 0,
                'atk_speed': operator_data.get('atk_speed', 1.0) or 1.0,
                'atk_type': operator_data.get('atk_type', '物伤') or '物伤',
                'block_count': operator_data.get('block_count', 1) or 1,
                'cost': operator_data.get('cost', 10) or 10
            }
            
            # 智能ID分配：寻找最小可用的ID
            next_id = self._find_next_available_id(cursor)
            
            # 使用指定的ID插入记录
            cursor.execute('''
                INSERT INTO operators (id, name, class_type, hp, atk, def, mdef, 
                                     atk_speed, atk_type, block_count, cost,
                                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        datetime('now','localtime'), datetime('now','localtime'))
            ''', (
                next_id,
                safe_data['name'],
                safe_data['class_type'],
                safe_data['hp'],
                safe_data['atk'],
                safe_data['def'],
                safe_data['mdef'],
                safe_data['atk_speed'],
                safe_data['atk_type'],
                safe_data['block_count'],
                safe_data['cost']
            ))
            
            conn.commit()
            
            logger.info(f"成功插入干员 {safe_data['name']} (智能分配ID: {next_id})")
            return next_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"插入干员失败: {e}")
            raise e
        finally:
            conn.close()
    
    def _find_next_available_id(self, cursor) -> int:
        """寻找下一个可用的ID
        
        此方法寻找最小的可用ID，实现删除后补位的功能。
        
        Args:
            cursor: 数据库游标
        Returns:
            int: 下一个可用的ID
        """
        try:
            # 获取所有现有的ID，按升序排列
            cursor.execute('SELECT id FROM operators ORDER BY id ASC')
            existing_ids = [row[0] for row in cursor.fetchall()]
            
            # 如果没有记录，从1开始
            if not existing_ids:
                return 1
            
            # 寻找第一个缺失的ID
            expected_id = 1
            for existing_id in existing_ids:
                if existing_id == expected_id:
                    expected_id += 1
                elif existing_id > expected_id:
                    # 找到了缺口，返回缺失的ID
                    return expected_id
                # 如果existing_id < expected_id，说明有重复，继续下一个
            
            # 如果没有缺口，返回下一个连续的ID
            return expected_id
            
        except Exception as e:
            logger.error(f"寻找可用ID失败: {e}")
            # 如果寻找失败，使用传统方式获取最大ID+1
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM operators')
            return cursor.fetchone()[0]
    
    def get_operator(self, operator_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取干员
        
        此方法用于根据干员ID从数据库中检索干员信息。
        
        Args:
            operator_id: 干员ID
        Returns:
            dict或None: 干员信息字典，若不存在则为None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM operators WHERE id = ?', (operator_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_operator_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取干员
        
        此方法用于根据干员名称从数据库中检索干员信息。
        
        Args:
            name: 干员名称
        Returns:
            dict或None: 干员信息字典，若不存在则为None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM operators WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_all_operators(self) -> List[Dict[str, Any]]:
        """获取所有干员
        
        此方法用于从数据库中检索所有干员信息。
        
        Returns:
            List[Dict[str, Any]]: 包含所有干员信息的列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM operators ORDER BY name')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def update_operator(self, operator_id: int, operator_data: Dict[str, Any]) -> bool:
        """更新干员数据 - 修复版本
        
        此方法增加了名称唯一性检查和时间修复，防止更新时出现约束冲突。
        
        Args:
            operator_id: 干员ID
            operator_data: 包含干员更新信息的字典
        Returns:
            bool: 是否更新成功
        Raises:
            Exception: 更新失败时抛出
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 首先验证操作数据，处理None值
            safe_data = {
                'name': operator_data.get('name', ''),
                'class_type': operator_data.get('class_type', '未知'),
                'hp': operator_data.get('hp', 0) or 0,
                'atk': operator_data.get('atk', 0) or 0,
                'def': operator_data.get('def', 0) or 0,
                'mdef': operator_data.get('mdef', 0) or 0,
                'atk_speed': operator_data.get('atk_speed', 1.0) or 1.0,
                'atk_type': operator_data.get('atk_type', '物伤') or '物伤',
                'block_count': operator_data.get('block_count', 1) or 1,
                'cost': operator_data.get('cost', 10) or 10
            }
            
            # 检查是否会导致名称冲突（除了当前干员）
            if safe_data['name']:
                cursor.execute('''
                    SELECT id FROM operators 
                    WHERE name = ? AND id != ?
                ''', (safe_data['name'], operator_id))
                
                existing = cursor.fetchone()
                if existing:
                    raise ValueError(f"干员名称 '{safe_data['name']}' 已被ID为{existing['id']}的干员使用，无法重复")
            
            # 检查目标干员是否存在
            cursor.execute('SELECT id FROM operators WHERE id = ?', (operator_id,))
            if not cursor.fetchone():
                raise ValueError(f"干员ID {operator_id} 不存在")
            
            # 执行更新（使用本地时间，添加updated_at）
            cursor.execute('''
                UPDATE operators 
                SET name=?, class_type=?, hp=?, atk=?, def=?, mdef=?, 
                    atk_speed=?, atk_type=?, block_count=?, cost=?
                WHERE id=?
            ''', (
                safe_data['name'],
                safe_data['class_type'],
                safe_data['hp'],
                safe_data['atk'],
                safe_data['def'],
                safe_data['mdef'],
                safe_data['atk_speed'],
                safe_data['atk_type'],
                safe_data['block_count'],
                safe_data['cost'],
                operator_id
            ))
            
            success = cursor.rowcount > 0  # 判断是否有行被更新
            conn.commit()
            
            if success:
                logger.info(f"成功更新干员 {safe_data['name']} (ID: {operator_id})")
            else:
                logger.warning(f"更新干员失败，没有找到ID为 {operator_id} 的干员")
            
            return success
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新干员失败: {e}")
            raise e
        finally:
            conn.close()
    
    def delete_operator(self, operator_id: int) -> bool:
        """删除干员
        
        此方法用于从数据库中删除指定干员ID的干员信息。
        
        Args:
            operator_id: 干员ID
        Returns:
            bool: 是否删除成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM operators WHERE id = ?', (operator_id,))
            success = cursor.rowcount > 0  # 判断是否有行被删除
            conn.commit()
            return success
        finally:
            conn.close()
    
    def delete_all_operators(self) -> Dict[str, Any]:
        """删除所有干员数据
        
        此方法用于删除数据库中的所有干员数据，并重置ID自增序列。
        同时删除相关的计算记录。
        
        Returns:
            Dict[str, Any]: 包含操作结果的字典
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 开始事务
            cursor.execute('BEGIN TRANSACTION')
            
            # 获取删除前的干员数量
            cursor.execute('SELECT COUNT(*) as count FROM operators')
            operator_count = cursor.fetchone()['count']
            
            # 删除所有相关的计算记录
            cursor.execute('DELETE FROM calculation_records WHERE operator_id IS NOT NULL')
            deleted_calc_records = cursor.rowcount
            
            # 删除所有干员
            cursor.execute('DELETE FROM operators')
            deleted_operators = cursor.rowcount
            
            # 重置自增ID序列
            cursor.execute('DELETE FROM sqlite_sequence WHERE name = "operators"')
            
            # 提交事务
            cursor.execute('COMMIT')
            
            result = {
                'success': True,
                'message': f'成功删除 {deleted_operators} 个干员和 {deleted_calc_records} 条计算记录',
                'deleted_operators': deleted_operators,
                'deleted_calc_records': deleted_calc_records
            }
            
            logger.info(f"删除所有干员完成: {result['message']}")
            return result
            
        except Exception as e:
            # 回滚事务
            cursor.execute('ROLLBACK')
            error_msg = f"删除所有干员失败: {e}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'deleted_operators': 0,
                'deleted_calc_records': 0
            }
        finally:
            conn.close()
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息
        
        此方法用于获取数据库的基本信息，包括干员数量、数据库路径和大小等。
        
        Returns:
            Dict[str, Any]: 包含数据库信息的字典
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT COUNT(*) as operator_count FROM operators')
            result = cursor.fetchone()
            
            return {
                'operator_count': result['operator_count'],  # 干员总数
                'database_path': self.db_path,               # 数据库文件路径
                'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0  # 数据库文件大小
            }
        finally:
            conn.close()
    
    def get_skills_by_operator(self, operator_id: int) -> List[Dict]:
        """
        获取干员技能列表
        
        Args:
            operator_id: 干员ID
            
        Returns:
            技能列表（当前简化版本返回空列表）
        Note:
            目前未实现技能系统，后续可扩展
        """
        # 简化版本：没有技能表，返回空列表
        # 如果将来需要技能系统，可以在这里实现
        return []
    
    def get_calculation_statistics(self) -> Dict[str, int]:
        """
        获取计算统计信息
        
        Returns:
            统计信息字典
        Note:
            目前仅返回干员数量和缓存大小等基础信息
        """
        try:
            # 获取基础统计
            operators = self.get_all_operators()
            
            return {
                'total_calculations': 0,  # 简化版本，暂时返回0
                'cache_size': len(getattr(self, 'calculation_cache', {})),
                'error_count': 0,  # 简化版本，暂时返回0
                'operator_count': len(operators)
            }
        except Exception:
            return {
                'total_calculations': 0,
                'cache_size': 0,
                'error_count': 0,
                'operator_count': 0
            }

    def close(self):
        """关闭数据库连接
        
        此方法用于关闭数据库连接。
        
        Note:
            - 调用者负责在完成后关闭连接
            - SQLite会自动管理连接，无需手动关闭
        """
        pass  # SQLite会自动管理连接 

    def reorder_operator_ids(self) -> Dict[str, Any]:
        """重新排列所有干员的ID，从1开始连续编号
        
        此方法用于重新排列数据库中所有干员的ID，从1开始连续编号。
        会处理相关的外键约束，确保数据一致性。
        
        Returns:
            Dict[str, Any]: 包含操作结果的字典
            
        Note:
            - 此方法会重新安排所有现有干员的ID
            - 同时更新相关表的外键引用
            - 操作会在事务中进行，确保数据一致性
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 开始事务
            cursor.execute('BEGIN TRANSACTION')
            
            # 获取所有干员，按ID排序以保持原有顺序
            cursor.execute('SELECT * FROM operators ORDER BY id ASC')
            operators = cursor.fetchall()
            
            if not operators:
                cursor.execute('COMMIT')
                return {
                    'success': True,
                    'message': '没有干员需要重排ID',
                    'reordered_count': 0,
                    'id_mapping': {}
                }
            
            # 创建ID映射表
            id_mapping = {}
            temp_updates = []
            
            # 第一步：将所有ID临时设置为负值，避免唯一约束冲突
            for i, operator in enumerate(operators):
                old_id = operator['id']
                temp_id = -(i + 1)  # 使用负数作为临时ID
                
                cursor.execute('UPDATE operators SET id = ? WHERE id = ?', (temp_id, old_id))
                temp_updates.append((temp_id, old_id, i + 1))
            
            # 第二步：将临时ID更新为最终的连续ID
            for temp_id, old_id, new_id in temp_updates:
                cursor.execute('UPDATE operators SET id = ? WHERE id = ?', (new_id, temp_id))
                id_mapping[old_id] = new_id
                
                # 同时更新计算记录表的外键引用
                cursor.execute('''
                    UPDATE calculation_records 
                    SET operator_id = ? 
                    WHERE operator_id = ?
                ''', (new_id, old_id))
            
            # 重置自增ID序列，确保下次插入从正确的ID开始
            cursor.execute('DELETE FROM sqlite_sequence WHERE name = "operators"')
            cursor.execute('INSERT INTO sqlite_sequence (name, seq) VALUES ("operators", ?)', (len(operators),))
            
            # 提交事务
            cursor.execute('COMMIT')
            
            result = {
                'success': True,
                'message': f'成功重排 {len(operators)} 个干员的ID (按原有ID顺序重新编号)',
                'reordered_count': len(operators),
                'id_mapping': id_mapping
            }
            
            logger.info(f"ID重排完成: {result['message']}")
            return result
            
        except Exception as e:
            # 回滚事务
            cursor.execute('ROLLBACK')
            error_msg = f"ID重排失败: {e}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'reordered_count': 0,
                'id_mapping': {}
            }
        finally:
            conn.close()
    
    def get_id_gaps(self) -> List[int]:
        """获取ID序列中的空缺
        
        Returns:
            List[int]: 缺失的ID列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM operators ORDER BY id ASC')
            existing_ids = [row[0] for row in cursor.fetchall()]
            
            if not existing_ids:
                return []
            
            # 找出所有缺失的ID
            gaps = []
            max_id = max(existing_ids)
            for i in range(1, max_id + 1):
                if i not in existing_ids:
                    gaps.append(i)
            
            return gaps
            
        except Exception as e:
            logger.error(f"获取ID空缺失败: {e}")
            return []
        finally:
            conn.close()
    
    def record_calculation(self, operator_id: Optional[int], calculation_type: str, 
                          parameters: Dict[str, Any], results: Dict[str, Any]) -> int:
        """记录计算操作 - 使用本地时间
        
        Args:
            operator_id: 干员ID，可为None
            calculation_type: 计算类型
            parameters: 计算参数（字典）
            results: 计算结果（字典）
        Returns:
            int: 新插入的计算记录ID
        Raises:
            Exception: 插入失败时抛出
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 使用本地时间而不是UTC时间
            cursor.execute('''
                INSERT INTO calculation_records (operator_id, calculation_type, parameters, results, created_at)
                VALUES (?, ?, ?, ?, datetime('now','localtime'))
            ''', (
                operator_id,
                calculation_type,
                json.dumps(parameters, ensure_ascii=False),
                json.dumps(results, ensure_ascii=False)
            ))
            
            record_id = cursor.lastrowid  # 获取新插入的记录ID
            conn.commit()
            return record_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_today_calculations(self) -> int:
        """获取今日计算次数
        
        此方法用于获取今日的计算次数。
        
        Returns:
            int: 今日计算次数
        Note:
            通过比较created_at字段的日期实现
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')  # 获取今天日期字符串
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM calculation_records 
                WHERE DATE(created_at) = ?
            ''', (today,))
            
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except Exception as e:
            print(f"获取今日计算次数失败: {e}")
            return 0
        finally:
            conn.close()
    
    def get_calculation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取计算历史记录
        
        此方法用于获取计算历史记录。
        
        Args:
            limit: 限制返回的记录数量
        Returns:
            List[Dict[str, Any]]: 计算历史记录列表
        Note:
            解析parameters和results字段为字典
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT cr.*, o.name as operator_name
                FROM calculation_records cr
                LEFT JOIN operators o ON cr.operator_id = o.id
                ORDER BY cr.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            records = []
            
            for row in rows:
                record = dict(row)
                # 解析JSON字段
                try:
                    record['parameters'] = json.loads(record['parameters']) if record['parameters'] else {}
                    record['results'] = json.loads(record['results']) if record['results'] else {}
                except:
                    record['parameters'] = {}
                    record['results'] = {}
                
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"获取计算历史失败: {e}")
            return []
        finally:
            conn.close()
    
    def record_import(self, import_type: str, file_name: str, record_count: int = 0, 
                     status: str = 'success', error_message: str = None) -> int:
        """记录导入操作 - 使用本地时间
        
        Args:
            import_type: 导入类型（如'excel_import'）
            file_name: 文件名
            record_count: 导入记录数量
            status: 导入状态
            error_message: 错误信息（可选）
        Returns:
            int: 新插入的导入记录ID
        Raises:
            Exception: 插入失败时抛出
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 使用本地时间而不是UTC时间
            cursor.execute('''
                INSERT INTO import_records (import_type, file_name, record_count, 
                                          status, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
            ''', (import_type, file_name, record_count, status, error_message))
            
            record_id = cursor.lastrowid  # 获取新插入的导入记录ID
            conn.commit()
            return record_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_import_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取导入记录
        
        此方法用于获取导入记录。
        
        Args:
            limit: 限制返回的记录数量
        Returns:
            List[Dict[str, Any]]: 导入记录列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM import_records 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"获取导入记录失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要
        
        此方法用于获取统计摘要。
        
        Returns:
            Dict[str, Any]: 包含统计信息的字典
        Note:
            包括干员总数、今日计算次数、导入记录总数、计算记录总数、职业分布等
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取基础统计
            summary = {}
            
            # 干员总数
            cursor.execute('SELECT COUNT(*) as count FROM operators')
            result = cursor.fetchone()
            summary['total_operators'] = result['count'] if result else 0
            
            # 今日计算次数
            summary['today_calculations'] = self.get_today_calculations()
            
            # 导入记录总数
            cursor.execute('SELECT COUNT(*) as count FROM import_records')
            result = cursor.fetchone()
            summary['total_imports'] = result['count'] if result else 0
            
            # 计算记录总数
            cursor.execute('SELECT COUNT(*) as count FROM calculation_records')
            result = cursor.fetchone()
            summary['total_calculations'] = result['count'] if result else 0
            
            # 职业分布
            cursor.execute('''
                SELECT class_type, COUNT(*) as count 
                FROM operators 
                GROUP BY class_type
            ''')
            class_distribution = {}
            for row in cursor.fetchall():
                class_distribution[row['class_type']] = row['count']
            summary['class_distribution'] = class_distribution
            
            return summary
            
        except Exception as e:
            print(f"获取统计摘要失败: {e}")
            return {
                'total_operators': 0,
                'today_calculations': 0,
                'total_imports': 0,
                'total_calculations': 0,
                'class_distribution': {}
            }
        finally:
            conn.close()
    
    def cleanup_old_records(self, days: int = 30):
        """清理旧记录
        
        此方法用于清理旧记录。
        
        Args:
            days: 保留的天数
        Returns:
            dict: 删除的计算记录和导入记录数量
        Note:
            计算记录保留30天，导入记录保留90天
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 清理30天前的计算记录
            cursor.execute('''
                DELETE FROM calculation_records 
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days))
            
            deleted_calculations = cursor.rowcount  # 被删除的计算记录数
            
            # 清理30天前的导入记录（保留更久的导入历史）
            cursor.execute('''
                DELETE FROM import_records 
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days * 3))  # 保留90天的导入记录
            
            deleted_imports = cursor.rowcount  # 被删除的导入记录数
            
            conn.commit()
            
            return {
                'deleted_calculations': deleted_calculations,
                'deleted_imports': deleted_imports
            }
            
        except Exception as e:
            conn.rollback()
            print(f"清理旧记录失败: {e}")
            return {'deleted_calculations': 0, 'deleted_imports': 0}
        finally:
            conn.close() 