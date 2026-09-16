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

        //World
        this.load.image('world-map', '/public/world/great-world.png');
        this.load.image('world-waypoint', '/public/world/effects/world-waypoint.png');
        this.load.image('world-selector', '/public/ui/world-selection.png');
        
        // UI
        this.load.image('btn-world-ui', '/public/ui/buttons/btn-world-enter.png');
        this.load.image('btn-world-ui-disabled', '/public/ui/buttons/btn-world-enter-disabled.png');
        this.load.image('btn-attack-ui', '/public/ui/buttons/btn-attack.png');
        this.load.image('btn-attack-ui-disabled', '/public/ui/buttons/btn-attack-disabled.png');
        this.load.image('btn-flee-ui', '/public/ui/buttons/btn-flee.png');
        this.load.image('btn-flee-ui-disabled', '/public/ui/buttons/btn-flee-disabled.png');

        //Scene acts
        this.load.image('act1-world-scene', '/public/world/world-scenes/act1-scenario.png');

        //Characters and sprites
        this.load.aseprite('player-sprite', '/public/sprites/player/Soldier.png', '/public/sprites/player/Soldier.json');
        this.load.aseprite('orc-creature-sprite', '/public/sprites/creature/Orc.png', '/public/sprites/creature/Orc.json');
    }
    create() {
        //this.anims.createFromAseprite('player-sprite');
        //this.anims.createFromAseprite('orc-creature-sprite');

        this.scene.start('WorldScene');
    }
}