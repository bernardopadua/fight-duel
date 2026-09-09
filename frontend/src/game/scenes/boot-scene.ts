import Phaser from 'phaser';

export class BootScene extends Phaser.Scene {
    constructor() {
        super({ key: 'BootScene' });
    }
    preload() {
        this.add.text(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            "Loading...",
            { color: '#ffffff', fontSize: '18px' },
        ).setOrigin(0.5);

        this.load.image('world-map', '/public/world/great-world.png');
        this.load.image('world-waypoint', '/public/world/effects/world-waypoint.png');
        this.load.image('world-selector', '/public/ui/world-selection.png');
        this.load.image('btn-world-select', '/public/ui/buttons/btn-world-enter.png')
        this.load.image('btn-world-select-disabled', '/public/ui/buttons/btn-world-enter-disabled.png')

        this.load.aseprite('player-sprite', '/public/sprites/player/Soldier.png', '/public/sprites/player/Soldier.json');
    }
    create() {
        this.scene.start('WorldScene');
    }
}