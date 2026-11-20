import math
import re
from collections import defaultdict
from pathlib import Path


root = Path('evidence/pr07')


def blocks(text, field):
    pattern = re.compile(r'^' + re.escape(field) + r' \{', re.M)
    for match in pattern.finditer(text):
        start = text.index('{', match.start())
        depth = 1
        end = start + 1
        while end < len(text) and depth:
            if text[end] == '{':
                depth += 1
            elif text[end] == '}':
                depth -= 1
            end += 1
        if depth == 0:
            yield text[start + 1:end - 1]


def components(block, field, names):
    match = re.search(
        r'\b' + re.escape(field) + r'\s*\{([^{}]*)\}',
        block,
        flags=re.S,
    )
    assert match is not None, f'Missing {field}'
    body = match.group(1)
    result = []
    for name in names:
        value = re.search(r'\b' + name + r':\s*([^\s}]+)', body)
        result.append(float(value.group(1)) if value else 0.0)
    return tuple(result)


def multiply(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (
        w*X + x*W + y*Z - z*Y,
        w*Y - x*Z + y*W + z*X,
        w*Z + x*Y - y*X + z*W,
        w*W - x*X - y*Y - z*Z,
    )


poses = defaultdict(list)
text = (root / 'physical-poses.txt').read_text()

for block in blocks(text, 'pose'):
    name = re.search(r'\bname:\s*"([^"]+)"', block)
    if name is None:
        continue
    poses[name.group(1)].append((
        components(block, 'position', 'xyz'),
        components(block, 'orientation', 'xyzw'),
    ))

model = poses['course_ackermann']
assert len(model) >= 2, 'Too few model poses'
start, finish = model[0][0], model[-1][0]
distance = math.hypot(finish[0] - start[0], finish[1] - start[1])

print(f'model_samples={len(model)}')
print(f'model_start_xyz={start}')
print(f'model_finish_xyz={finish}')
print(f'physical_displacement_m={distance:.6f}')
assert 0.05 < distance < 1.0, 'Unexpected physical displacement'

for name in (
    'front_left_wheel', 'front_right_wheel',
    'rear_left_wheel', 'rear_right_wheel',
):
    samples = poses[name]
    assert len(samples) >= 2, f'Missing wheel samples: {name}'

    initial = samples[0][1]
    final = samples[-1][1]
    inverse = (-initial[0], -initial[1], -initial[2], initial[3])
    relative = multiply(final, inverse)
    norm = math.sqrt(sum(value * value for value in relative))
    assert norm > 0
    relative = tuple(value / norm for value in relative)

    vector_norm = math.sqrt(sum(value * value for value in relative[:3]))
    angle = 2 * math.atan2(vector_norm, abs(relative[3]))
    axis_y_abs = abs(relative[1]) / vector_norm if vector_norm else 0.0

    print(
        f'{name}: relative_angle_rad={angle:.6f}; '
        f'abs_axis_y={axis_y_abs:.6f}'
    )
    assert angle > 0.2, f'No clear wheel rotation: {name}'
    assert axis_y_abs > 0.95, f'Unexpected rotation axis: {name}'

ros_text = (root / 'ros-drive-messages.txt').read_text()
ros_speeds = [
    float(match.group(1))
    for match in re.finditer(
        r'^linear:\s*\n\s+x:\s*([^\s]+)', ros_text, re.M
    )
]

gz_text = (root / 'gazebo-drive-messages.txt').read_text()
gz_speeds = []
for block in blocks(gz_text, 'linear'):
    match = re.search(r'\bx:\s*([^\s}]+)', block)
    gz_speeds.append(float(match.group(1)) if match else 0.0)

assert ros_speeds and gz_speeds
for label, speeds in [('ROS', ros_speeds), ('Gazebo', gz_speeds)]:
    assert all(math.isfinite(speed) for speed in speeds)
    moving = sum(
        math.isclose(speed, 0.2, abs_tol=1e-6)
        for speed in speeds
    )
    assert moving > 0, f'No 0.2 m/s command on {label}'
    assert math.isclose(speeds[-1], 0.0, abs_tol=1e-6)
    print(
        f'{label}: messages={len(speeds)}; '
        f'commands_at_0.2_mps={moving}; final_speed={speeds[-1]}'
    )

print('PASS: 0.2 m/s command observed on ROS and Gazebo sides')
print('PASS: physical model displacement verified')
print('PASS: all four wheels rotated about transverse axes')
