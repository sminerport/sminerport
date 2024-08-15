#!/bin/bash

echo '<!-- Most Used Languages Centered -->' > README.md
echo '<p align="center">' >> README.md
echo '<img src="https://github-readme-stats.vercel.app/api/top-langs/?username=sminerport&layout=compact&theme=default&token=${GH_README_STATS_TOKEN}" alt="Top Languages" />' >> README.md
echo '</p>' >> README.md

# GitHub Stats Centered
echo '<!-- GitHub Stats Centered -->' >> README.md
echo '<p align="center">' >> README.md
echo '<img src="https://github-readme-stats.vercel.app/api?username=sminerport&show_icons=true&theme=default&count_private=true&token=${GH_TOKEN}" alt="GitHub Stats" />' >> README.md
echo '</p>' >> README.md

# Trophies Centered
echo '<!-- Trophies Centered -->' >> README.md
echo '<p align="center">' >> README.md
echo '<img src="https://github-profile-trophy.vercel.app/?username=sminerport&theme=flat&no-frame=true&margin-w=15" alt="Trophies" />' >> README.md
echo '</p>' >> README.md

# Snake Game Centered
echo '<!-- Snake Game Centered -->' >> README.md
echo '<p align="center">' >> README.md
echo '<img src="https://raw.githubusercontent.com/sminerport/snk/output/github-contribution-grid-snake.svg" alt="Snake Game" />' >> README.md
echo '</p>' >> README.md
