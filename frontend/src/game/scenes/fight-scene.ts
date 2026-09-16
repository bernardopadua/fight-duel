import Phaser from 'phaser';

// WSocket MESSAGES
import type { WebSocketFightUpdate } from '@/game/services/ws-messages';

// OBJECTS
import { ImageButton } from '@/game/objects/image-button';

// EVENTBUS
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

// SERVICES
import type { GameServices } from '@/game/game-context';

interface FightData {
    creatureName: string;
    creatureLevel: number;
    scenarioName: string;
}

export class FightScene extends Phaser.Scene {
    private creatureData! : FightData;
    
    // Player
    private activePlayer! : Phaser.GameObjects.Sprite;

    // Creature
    private activeCreature! : Phaser.GameObjects.Sprite;

    // UI
    private btnAttack: ImageButton;
    private btnFlee: ImageButton;

    constructor() {
        super({ key: "FightScene" });
    }
    init(data: FightData) {
        this.creatureData = data;
    }
    preload() {
    }
    createButtons() {
        this.btnAttack = new ImageButton(
            this,
            this.cameras.main.centerX - 100, 
            this.cameras.main.centerY + 200, 
            'btn-attack-ui',
            'btn-attack-ui-disabled',
            '',
            {width: 200, height: 50}
        ).setVisible(false).setDepth(2);

        this.btnFlee = new ImageButton(
            this,
            this.cameras.main.centerX + 100, 
            this.cameras.main.centerY + 200, 
            'btn-flee-ui',
            'btn-flee-ui-disabled',
            '',
            {width: 200, height: 50}
        ).setVisible(false).setDepth(2);

    }
    createEventsForScene() {
        const {width} = this.scale;
        const onFightUpdate = (data: WebSocketFightUpdate["data"]) => {
            if (data.isCreatureAttacking){
                this.activeCreature.play({key: 'Walk', repeat: -1});
                this.tweens.add({
                    targets: this.activeCreature,
                    ease: 'Power1',
                    x: this.activePlayer.x + this.activePlayer.width,
                    onComplete: () => {
                        this.activeCreature.play({key: 'Attack'});
                        this.activePlayer.play({key: 'Hurt'});
                        this.activeCreature.setFlipX(true);
                        this.tweens.add({
                            targets: this.activeCreature,
                            x: width - 450,
                            ease: 'Power1',
                            onComplete: () => {
                                this.activeCreature.setFlipX(true);
                                this.activeCreature.play({key: 'Idle', repeat: -1});
                            }
                        });
                    }
                });
            }
            if (data.isPlayerAttacking){
                this.activePlayer.play({key: 'Walk', repeat: -1});
                this.tweens.add({
                    targets: this.activePlayer,
                    ease: 'Power1',
                    x: this.activeCreature.x,
                    onComplete: () => {
                        this.activePlayer.play({key: 'Attack'});
                        this.activeCreature.play({key: 'Hurt'});
                        this.activePlayer.setFlipX(true);
                        this.activePlayer.play({key: 'Walk', repeat: -1});
                        this.tweens.add({
                            targets: this.activePlayer,
                            x: 450,
                            ease: 'Power1',
                            onComplete: () => {
                                this.activePlayer.setFlipX(true);
                                this.activePlayer.play({key: 'Idle', repeat: -1});
                            }
                        });
                    }
                });
            }
        };
        EventBus.on(GAME_EVENTS.FIGHT_UPDATE, onFightUpdate);

        const cleanUp = () => {
            EventBus.off(GAME_EVENTS.FIGHT_UPDATE, onFightUpdate);
        };
        this.events.once(Phaser.Scenes.Events.SHUTDOWN, cleanUp);
        this.events.once(Phaser.Scenes.Events.DESTROY, cleanUp);
    }
    create() {
        const gameServices = this.registry.get('services') as GameServices;

        const { width, height } = this.scale;
        
        if(!this.creatureData){
            console.error('No creature.');
            this.scene.start('WorldScene');
            return;
        }

        //Scenario setup;
        this.add.image(0, 0, this.creatureData.scenarioName).setDisplaySize(
            width, height
        ).setOrigin(0, 0);

        //Adding characters
        this.activePlayer = this.add.sprite(-50, (height/2), 'player-sprite').setScale(
            2.5, 2.5
        ).setDepth(1);
        this.activePlayer.anims.createFromAseprite('player-sprite');

        this.activeCreature = this.add.sprite(width-450, height/2, 'orc-creature-sprite').setScale(
            2.5, 2.5
        ).setDepth(1).setFlipX(true);
        this.activeCreature.anims.createFromAseprite('orc-creature-sprite');
        this.activeCreature.play({key: 'Idle', repeat: -1})

        //Buttons
        this.createButtons();
        this.btnAttack.setVisible(true);
        this.btnFlee.setVisible(true);

        this.btnFlee.setOnClick(()=>{
            gameServices.fightService.flee();
        });

        //Tweens
        this.activePlayer.play({ key: 'Walk', repeat: -1 });
        this.tweens.add({
            targets: this.activePlayer,
            x: 450,
            duration: 1000,
            ease: 'Power1',
            onComplete: () => {
                this.activePlayer.play({ key: 'Idle', repeat: -1 });
            }
        });

        this.input.keyboard?.once('keydown-SPACE', ()=>{
            this.scene.start('WorldScene');
        });
    }
}