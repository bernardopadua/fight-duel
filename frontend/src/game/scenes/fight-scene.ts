import Phaser from 'phaser';

// WSocket MESSAGES
import type { 
    WebSocketFightUpdate, 
    WebSocketFightFinish,
    WebSocketFightDropItems,
    WebSocketPlayerReviveCooldown
} from '@/game/services/ws-messages';

// OBJECTS
import { ImageButton } from '@/game/objects/image-button';
import { StatusBar } from '@/game/objects/status-bar';

// EVENTBUS
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

//STORES
import { usePlayerStore } from '@/game/store/player-store';
import { useDropStore } from '@/game/store/drop-store';
import { useUIStore } from '@/game/store/ui-store';

// SERVICES
import type { GameServices } from '@/game/game-context';


interface FightData {
    creatureName: string;
    creatureLevel: number;
    creatureLife: number;
    creatureMaxLife: number;
    scenarioName: string;
}

export class FightScene extends Phaser.Scene {
    private creatureData! : FightData;
    
    // Player
    private activePlayer! : Phaser.GameObjects.Sprite;
    private lifePlayerStatus! : StatusBar;
    private staminaPlayerStatus! : StatusBar;

    // Creature
    private activeCreature! : Phaser.GameObjects.Sprite;
    private lifeCreatureStatus! : StatusBar;

    private eventEqueue: Array<() => Promise<void>> = [];
    private isProcessing: boolean = false;

    // UI
    private btnAttack: ImageButton;
    private btnFlee: ImageButton;
    private btnLeave: ImageButton;

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
        this.btnLeave = new ImageButton(
            this,
            this.cameras.main.centerX, 
            this.cameras.main.centerY + 200, 
            'btn-world-ui',
            'btn-world-ui-disabled',
            'Leave',
            {
                width: 300, height: 67,
                textStyle: {
                    fontFamily: 'Georgia',
                    fontSize: '18px'
                }
            }
        ).setVisible(false).setDepth(2);
    }
    async processEventEqueue(){
        if (this.isProcessing) return;
        this.isProcessing = true;

        while (this.eventEqueue.length > 0){
            const nextAction = this.eventEqueue.shift();
            if (!nextAction) break;
            await nextAction();
        }

        this.isProcessing = false;
    }
    createEventsForScene() {
        const {width} = this.scale;

        const onFightUpdate = (data: WebSocketFightUpdate["data"]) => {
            const creatureAttacking = () => new Promise<void>((resolve) => {
                this.activeCreature.play({key: 'Walk', repeat: -1});
                this.tweens.add({
                    targets: this.activeCreature,
                    ease: 'Power1',
                    duration: 250,
                    x: this.activePlayer.x + (this.activePlayer.width/2),
                    onComplete: () => {
                        this.activeCreature.play({key: 'Attack01'}, true);
                        this.activePlayer.play({key: 'Hurt', timeScale: 1.5});
                        
                        const damage = data.creatureAttackDamage;
                        const damageTaken = this.add.text(
                            this.activePlayer.x, this.activePlayer.y, 
                            damage.toString(), {fontSize: '24px', color: '#a34a4aff'}).setDepth(
                                2
                        );

                        this.tweens.add({
                            targets: damageTaken,
                            y: this.activePlayer.y - 100,
                            alpha: 0.01,
                            onComplete: () => {
                                damageTaken.destroy();
                                usePlayerStore.getState().setPlayerLife(data.playerLife);
                                this.lifePlayerStatus.update(data.playerLife, null);
                            }
                        });

                        this.activePlayer.once('animationcomplete-Hurt', ()=>{
                            this.activeCreature.play({key: 'Walk', repeat: -1});
                            this.activeCreature.setFlipX(false);
                            this.tweens.add({
                                targets: this.activeCreature,
                                x: width - 450,
                                ease: 'Power1',
                                duration: 300,
                                onComplete: () => {
                                    this.activeCreature.setFlipX(true);
                                    this.activeCreature.play({key: 'Idle', repeat: -1});
                                    this.activePlayer.play({key: 'Idle', repeat: -1});
                                    resolve();
                                }
                            });
                        });
                    }
                });
            });

            const playerAttacking = () => new Promise<void>((resolve) => {
                this.activePlayer.play({key: 'Walk', repeat: -1});
                this.tweens.add({
                    targets: this.activePlayer,
                    ease: 'Power1',
                    duration: 250,
                    x: this.activeCreature.x - (this.activeCreature.width/2),
                    onComplete: () => {
                        this.activePlayer.play({key: 'Attack01'}, true);
                        this.activeCreature.play({key: 'Hurt', timeScale: 1.5});

                        const damage = data.playerAttackDamage;
                        const damageTaken = this.add.text(
                            this.activePlayer.x, this.activePlayer.y, 
                            damage.toString(), {fontSize: '24px', color: '#a34a4aff'}).setDepth(
                                2
                        );

                        this.tweens.add({
                            targets: damageTaken,
                            y: this.activePlayer.y - 100,
                            alpha: 0.01,
                            onComplete: () => {
                                this.creatureData.creatureLife = data.creatureLife;
                                this.lifeCreatureStatus.update(this.creatureData.creatureLife, null);
                                this.staminaPlayerStatus.update(data.playerStamina, null);
                                damageTaken.destroy();
                            }
                        });

                        this.activeCreature.once('animationcomplete-Hurt', ()=>{
                            this.activePlayer.play({key: 'Walk', repeat: -1});
                            this.activePlayer.setFlipX(true);
                            this.tweens.add({
                                targets: this.activePlayer,
                                x: 450,
                                ease: 'Power1',
                                duration: 300,
                                onComplete: () => {
                                    this.activePlayer.setFlipX(false);
                                    this.activePlayer.play({key: 'Idle', repeat: -1});
                                    if (this.lifeCreatureStatus.getValue() > 0){
                                        this.activeCreature.play({key: 'Idle', repeat: -1});
                                    }
                                    resolve();
                                }
                            });
                        });
                    }
                });
            });

            if (data.isCreatureAttacking){
                this.eventEqueue.push(creatureAttacking);
            }

            if (data.isPlayerAttacking){
                this.eventEqueue.push(playerAttacking);
            }

            this.processEventEqueue();
        };

        const onFightFinish = (data: WebSocketFightFinish["data"]) => {
            if (!data.isPlayerAlive){
                const playerIsDead = () => new Promise<void>((resolve) => {
                    this.activePlayer.play({key: 'Death'});
                    this.activePlayer.once('animationcomplete-Death', ()=>{
                        setTimeout(() => {
                            this.tweens.add({
                                targets: this.activePlayer,
                                alpha: 0.01,
                                duration: 2500,
                                y: this.activePlayer.y - 400,
                                onComplete: () => {
                                    this.scene.stop();
                                }
                            });
                            resolve();
                        }, 3000);
                    });
                });
                this.eventEqueue.push(playerIsDead);
            } else if(data.isPlayerAlive && !data.isMonsterAlive) {
                const playerWin = () => new Promise<void>((resolve) => {
                    //Assuring no tweens is running
                    const activeCreatureTweens = this.tweens.getTweensOf(this.activeCreature);
                    if (activeCreatureTweens.length > 0){
                        activeCreatureTweens[activeCreatureTweens.length -1].once('complete', () => {
                            this.activeCreature.play({key: 'Death'});
                            this.activeCreature.once('animationcomplete-Death', ()=>{
                                this.btnAttack.setVisible(false);
                                this.btnFlee.setVisible(false);
                                this.btnLeave.setVisible(true);
                                resolve();
                            });
                        });
                    } else {
                        this.activeCreature.play({key: 'Death'});
                        this.activeCreature.once('animationcomplete-Death', ()=>{
                            this.btnAttack.setVisible(false);
                            this.btnFlee.setVisible(false);
                            this.btnLeave.setVisible(true);
                            resolve();
                        });
                    }
                });                
                this.eventEqueue.push(playerWin);
            } else if(data.isPlayerAlive && data.isMonsterAlive){
                this.activePlayer.setFlipX(true);
                this.activePlayer.play({key: 'Walk', repeat: -1});
                this.tweens.add({
                    targets: this.activePlayer,
                    x: -250,
                    ease: 'Power1',
                    duration: 350,
                    onComplete: () => {
                        this.scene.wake('WorldScene');
                        this.scene.stop();
                    }
                });
            }
        };

        const onFightDropItems = (data: WebSocketFightDropItems['data']) => {
            useDropStore.getState().setItems(data);
            useUIStore.getState().setInitialPosition(
                'dropItems',
                {x: window.innerWidth/2 - 150, y: window.innerHeight/2 - 150}
            );
            useUIStore.getState().open('dropItems');
        };

        const onPlayerReviveCooldown = (data: WebSocketPlayerReviveCooldown["data"]) => {
            this.scene.wake('WorldScene');
            const worldScene = this.scene.get('WorldScene') as any;
            worldScene.reviveCooldown = data;
            worldScene.showDeathScreen();
        }

        const updatePlayerLifeAfterRecover = () => {
            const player = usePlayerStore.getState().player;
            this.lifePlayerStatus.update(player.playerLife, player.playerMaxLife);
            this.staminaPlayerStatus.update(player.playerStamina, player.playerMaxStamina);
        }

        EventBus.on(GAME_EVENTS.FIGHT_DROP_ITEMS, onFightDropItems);
        EventBus.on(GAME_EVENTS.FIGHT_UPDATE, onFightUpdate);
        EventBus.on(GAME_EVENTS.FIGHT_FINISH, onFightFinish);
        EventBus.on(GAME_EVENTS.PLAYER_REVIVE_COOLDOWN, onPlayerReviveCooldown);
        EventBus.on(GAME_EVENTS.PLAYER_RECOVER_STATUS, updatePlayerLifeAfterRecover);
    

        const cleanUp = () => {
            EventBus.off(GAME_EVENTS.FIGHT_UPDATE, onFightUpdate);
            EventBus.off(GAME_EVENTS.FIGHT_FINISH, onFightFinish);
            EventBus.off(GAME_EVENTS.FIGHT_DROP_ITEMS, onFightDropItems);
            EventBus.off(GAME_EVENTS.PLAYER_REVIVE_COOLDOWN, onPlayerReviveCooldown);
            EventBus.off(GAME_EVENTS.PLAYER_RECOVER_STATUS, updatePlayerLifeAfterRecover);
        };
        this.events.once(Phaser.Scenes.Events.SHUTDOWN, cleanUp);
        this.events.once(Phaser.Scenes.Events.DESTROY, cleanUp);
    }
    create() {
        const gameServices = this.registry.get('services') as GameServices;

        const { width, height } = this.scale;
        
        if(!this.creatureData){
            console.error('No creature.');
            this.scene.wake('WorldScene');
            this.scene.stop();
            return;
        }

        //Scenario setup;
        this.add.image(0, 0, this.creatureData.scenarioName).setDisplaySize(
            width, height
        ).setOrigin(0, 0);

        //Adding events
        this.createEventsForScene();

        //Adding characters
        const player = usePlayerStore.getState().player;
        this.activePlayer = this.add.sprite(-50, (height/2), 'player-sprite').setScale(
            2.5, 2.5
        ).setDepth(1);
        this.activePlayer.anims.createFromAseprite('player-sprite');
        this.lifePlayerStatus = new StatusBar(this, this.activePlayer, 10, 0x22c55e, 64, 8);
        this.staminaPlayerStatus = new StatusBar(this, this.activePlayer, -5, 0x14b8a6, 64, 8);
        this.lifePlayerStatus.update(player.playerLife, player.playerMaxLife);
        this.staminaPlayerStatus.update(player.playerStamina, player.playerMaxStamina);

        this.activeCreature = this.add.sprite(width-450, height/2, 'orc-creature-sprite').setScale(
            2.5, 2.5
        ).setDepth(1).setFlipX(true);
        this.activeCreature.anims.createFromAseprite('orc-creature-sprite');
        this.lifeCreatureStatus = new StatusBar(this, this.activeCreature, 15, 0x22c55e, 64, 8);
        this.lifeCreatureStatus.update(this.creatureData.creatureLife, this.creatureData.creatureMaxLife);
        this.activeCreature.play({key: 'Idle', repeat: -1})

        //Buttons
        this.createButtons();
        this.btnAttack.setVisible(true);
        this.btnFlee.setVisible(true);

        this.btnAttack.setOnClick(()=>{
            gameServices.fightService.attack();
        });
        this.btnFlee.setOnClick(()=>{
            gameServices.fightService.flee();
        });
        this.btnLeave.setOnClick(()=>{
            this.activePlayer.setFlipX(true);
            this.activePlayer.play({key: 'Walk', repeat: -1});
            this.tweens.add({
                targets: this.activePlayer,
                x: -250,
                ease: 'Power1',
                duration: 350,
                onComplete: () => {
                    this.scene.wake('WorldScene');
                    this.scene.stop();
                }
            });
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
    }
    
}