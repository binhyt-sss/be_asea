"""
Seed database with sample data for testing
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from database.session import AsyncSessionLocal
from database.models import User, WorkingZone
from loguru import logger


async def seed_database():
    """Create sample zones and users"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Create Working Zones
            zones_data = [
                {
                    "zone_id": "ZONE_001",
                    "zone_name": "Assembly Area A",
                    "x1": 0.0, "y1": 0.0,
                    "x2": 100.0, "y2": 0.0,
                    "x3": 100.0, "y3": 100.0,
                    "x4": 0.0, "y4": 100.0
                },
                {
                    "zone_id": "ZONE_002",
                    "zone_name": "Warehouse Section B",
                    "x1": 120.0, "y1": 0.0,
                    "x2": 250.0, "y2": 0.0,
                    "x3": 250.0, "y3": 150.0,
                    "x4": 120.0, "y4": 150.0
                },
                {
                    "zone_id": "ZONE_003",
                    "zone_name": "Office Area C",
                    "x1": 0.0, "y1": 120.0,
                    "x2": 80.0, "y2": 120.0,
                    "x3": 80.0, "y3": 200.0,
                    "x4": 0.0, "y4": 200.0
                },
                {
                    "zone_id": "ZONE_004",
                    "zone_name": "Parking Lot D",
                    "x1": 100.0, "y1": 120.0,
                    "x2": 250.0, "y2": 120.0,
                    "x3": 250.0, "y3": 250.0,
                    "x4": 100.0, "y4": 250.0
                },
                {
                    "zone_id": "ZONE_005",
                    "zone_name": "Security Gate E",
                    "x1": 270.0, "y1": 0.0,
                    "x2": 320.0, "y2": 0.0,
                    "x3": 320.0, "y3": 50.0,
                    "x4": 270.0, "y4": 50.0
                }
            ]
            
            logger.info("Creating working zones...")
            for zone_data in zones_data:
                zone = WorkingZone(**zone_data)
                session.add(zone)
            
            await session.flush()
            logger.success(f"✅ Created {len(zones_data)} zones")
            
            # Create Users
            users_data = [
                {"global_id": 1001, "name": "Nguyễn Văn An", "zone_id": "ZONE_001"},
                {"global_id": 1002, "name": "Trần Thị Bình", "zone_id": "ZONE_001"},
                {"global_id": 1003, "name": "Lê Văn Cường", "zone_id": "ZONE_001"},
                {"global_id": 1004, "name": "Phạm Thị Dung", "zone_id": "ZONE_002"},
                {"global_id": 1005, "name": "Hoàng Văn Em", "zone_id": "ZONE_002"},
                {"global_id": 1006, "name": "Đỗ Thị Phương", "zone_id": "ZONE_002"},
                {"global_id": 1007, "name": "Vũ Văn Giang", "zone_id": "ZONE_002"},
                {"global_id": 1008, "name": "Mai Thị Hà", "zone_id": "ZONE_003"},
                {"global_id": 1009, "name": "Bùi Văn Hùng", "zone_id": "ZONE_003"},
                {"global_id": 1010, "name": "Đinh Thị Lan", "zone_id": "ZONE_004"},
                {"global_id": 1011, "name": "Trương Văn Minh", "zone_id": "ZONE_004"},
                {"global_id": 1012, "name": "Lý Thị Nga", "zone_id": "ZONE_004"},
                {"global_id": 1013, "name": "Phan Văn Oanh", "zone_id": "ZONE_005"},
                {"global_id": 1014, "name": "Hồ Thị Phương", "zone_id": "ZONE_005"},
                {"global_id": 1015, "name": "Đặng Văn Quang", "zone_id": None},  # Not assigned
                {"global_id": 1016, "name": "Võ Thị Rạng", "zone_id": None},
                {"global_id": 1017, "name": "Cao Văn Sơn", "zone_id": None},
                {"global_id": 1018, "name": "Dương Thị Tâm", "zone_id": "ZONE_001"},
                {"global_id": 1019, "name": "Nông Văn Uy", "zone_id": "ZONE_002"},
                {"global_id": 1020, "name": "La Thị Vân", "zone_id": "ZONE_003"},
                {"global_id": 1021, "name": "Tạ Văn Xuân", "zone_id": "ZONE_004"},
                {"global_id": 1022, "name": "Lâm Thị Yến", "zone_id": "ZONE_005"},
                {"global_id": 1023, "name": "Kim Văn Zung", "zone_id": "ZONE_001"},
                {"global_id": 1024, "name": "Mạc Thị Ánh", "zone_id": "ZONE_002"},
                {"global_id": 1025, "name": "Châu Văn Bảo", "zone_id": "ZONE_003"},
            ]
            
            logger.info("Creating users...")
            for user_data in users_data:
                user = User(**user_data)
                session.add(user)
            
            await session.commit()
            logger.success(f"✅ Created {len(users_data)} users")
            
            # Summary
            logger.info("=" * 60)
            logger.success("🎉 Database seeded successfully!")
            logger.info(f"   - Zones: {len(zones_data)}")
            logger.info(f"   - Users: {len(users_data)}")
            logger.info(f"   - Unassigned Users: {sum(1 for u in users_data if u['zone_id'] is None)}")
            logger.info("=" * 60)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error seeding database: {e}")
            raise
        finally:
            await session.close()


async def clear_database():
    """Clear all data from database"""
    async with AsyncSessionLocal() as session:
        try:
            # Delete all users first (due to foreign key)
            from sqlalchemy import delete
            await session.execute(delete(User))
            await session.execute(delete(WorkingZone))
            await session.commit()
            logger.success("✅ Database cleared")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error clearing database: {e}")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        logger.info("Clearing database...")
        asyncio.run(clear_database())
    else:
        logger.info("Seeding database with sample data...")
        asyncio.run(seed_database())
