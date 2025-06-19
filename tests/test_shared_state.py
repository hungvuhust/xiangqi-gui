#!/usr/bin/env python3
"""
Test script để demo shared state functionality
"""

from src.utils.shared_state import shared_game_state, update_from_gui, get_for_ros
import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_shared_state():
    """Test shared state functionality"""
    print("🧪 Testing Shared State functionality...")

    # Test 1: Update from "GUI"
    print("\n1. Simulating GUI update...")
    fake_engine_results = {
        'Fairy-Stockfish': {
            'bestmove': 'e2e4',
            'evaluation': 0.5,
            'depth': 8,
            'nodes': 1000,
            'status': 'ready'
        }
    }

    update_from_gui(
        fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
        current_player="red",
        moves=["e2e4", "e9e8"],
        engine_results=fake_engine_results
    )

    print("✅ Updated shared state from simulated GUI")

    # Test 2: Read from "ROS"
    print("\n2. Reading from ROS perspective...")
    ros_data = get_for_ros()

    print(f"📋 FEN: {ros_data.get('fen', 'N/A')}")
    print(f"🎯 Current Player: {ros_data.get('current_player', 'N/A')}")
    print(f"📊 Move Count: {ros_data.get('move_count', 0)}")
    print(f"🤖 Best Move: {ros_data.get('best_move', 'N/A')}")
    print(
        f"🔧 Engine Results: {len(ros_data.get('engine_results', {}))} engines")

    # Test 3: Update engine results only
    print("\n3. Updating engine results...")
    time.sleep(1)

    new_engine_results = {
        'Fairy-Stockfish': {
            'bestmove': 'e4e5',
            'evaluation': 0.8,
            'depth': 10,
            'nodes': 5000,
            'status': 'ready'
        },
        'Pikafish': {
            'bestmove': 'e4e6',
            'evaluation': 0.3,
            'depth': 8,
            'nodes': 3000,
            'status': 'ready'
        }
    }

    shared_game_state.update_engine_results(new_engine_results)

    # Test 4: Read updated data
    print("\n4. Reading updated data...")
    ros_data2 = get_for_ros()

    print(f"🤖 New Best Move: {ros_data2.get('best_move', 'N/A')}")
    print(
        f"🔧 Engine Results: {len(ros_data2.get('engine_results', {}))} engines")

    for engine_name, result in ros_data2.get('engine_results', {}).items():
        bestmove = result.get('bestmove', 'N/A')
        evaluation = result.get('evaluation', 0)
        depth = result.get('depth', 0)
        print(
            f"  - {engine_name}: {bestmove} (eval: {evaluation:.2f}, depth: {depth})")

    # Test 5: Data freshness
    print("\n5. Testing data freshness...")
    print(f"📅 Data is fresh: {shared_game_state.is_data_fresh()}")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_shared_state()
