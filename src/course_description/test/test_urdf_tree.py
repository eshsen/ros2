"""Структурные проверки URDF: связность и parent lidar_link."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

URDF_XACRO = Path(__file__).resolve().parents[1] / 'urdf' / 'vehicle.urdf.xacro'


def _process_xacro() -> str:
    xacro = pytest.importorskip('xacro')
    return xacro.process_file(str(URDF_XACRO)).toxml()


def test_xacro_expands() -> None:
    xml = _process_xacro()
    assert 'base_link' in xml
    assert 'lidar_link' in xml


def test_lidar_parent_is_base_link() -> None:
    root = ET.fromstring(_process_xacro())
    joint = root.find("./joint[@name='lidar_link_joint']")
    assert joint is not None
    parent = joint.find('parent')
    assert parent is not None
    assert parent.get('link') == 'base_link'


def test_sensor_frames_present() -> None:
    root = ET.fromstring(_process_xacro())
    names = {link.get('name') for link in root.findall('link')}
    assert {'base_link', 'camera_link', 'lidar_link', 'imu_link'} <= names


def test_tree_is_connected_and_acyclic() -> None:
    root = ET.fromstring(_process_xacro())
    link_names = [link.get('name') for link in root.findall('link')]
    assert len(link_names) == len(set(link_names))
    links = set(link_names)
    edges = {name: [] for name in links}
    children = []

    for joint in root.findall('joint'):
        parent = joint.find('parent').get('link')
        child = joint.find('child').get('link')
        assert parent in links
        assert child in links
        assert parent != child
        edges[parent].append(child)
        children.append(child)

    assert len(children) == len(set(children))
    assert links - set(children) == {'base_link'}

    visited = set()

    def visit(name):
        assert name not in visited
        visited.add(name)
        for child in edges[name]:
            visit(child)

    visit('base_link')
    assert visited == links


def test_sensor_origins_match_contract() -> None:
    root = ET.fromstring(_process_xacro())

    for name in ('camera_link', 'lidar_link', 'imu_link'):
        joint = root.find(f"./joint[@name='{name}_joint']")
        assert joint is not None
        assert joint.get('type') == 'fixed'
        assert joint.find('parent').get('link') == 'base_link'

        origin = joint.find('origin')
        xyz = [float(value) for value in origin.get('xyz').split()]
        rpy = [float(value) for value in origin.get('rpy').split()]
        assert xyz == pytest.approx([0.28, 0.0, 0.38])
        assert rpy == pytest.approx([0.0, 0.0, 0.0])
