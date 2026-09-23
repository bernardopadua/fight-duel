// PHASER
import Phaser from 'phaser';

// DATA
import regionsHighlight from '@/game/data/regions-highligh.json';

// STORE
import { useWorldStore } from '@/game/store/world-store';
import { usePlayerStore } from '@/game/store/player-store';

// COMPONENTS
import { ImageButton } from '@/game/objects/image-button';

// EVENTBUS
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

// TYPES
import type { GameServices } from '@/game/game-context';
import type { WorldInfo } from '@/game/types';
import type { WebSocketFightMessage } from '@/game/services/ws-messages';

interface WorldSceneActiveTweens {
    waypoint: Phaser.Tweens.Tween;
    regionHighLight: Phaser.GameObjects.Arc;
}

export class WorldScene extends Phaser.Scene {
    private activeHero?: Phaser.GameObjects.Sprite;
    private activeWorldWaypoint?: Phaser.GameObjects.Arc;
    
    //Components
    private enterWorldBtn!: ImageButton;
    private leaveWorldBtn!: ImageButton;
    private moveInWorldBtn!: ImageButton;

    private activeWorld: WorldInfo | null = null;
    private activeWorldFightScene: string;
    private selectedWorldId: number = 0;
    private selectedWorldScene: string;

    private worldTweens: Map<number, WorldSceneActiveTweens> = new Map<number, WorldSceneActiveTweens>();

    constructor() {
        super({ key: 'WorldScene' });
    }
    preload() {
    }
    createTextures() {
        if (!this.textures.exists('soft-glow')) {
            const canvas = this.textures.createCanvas('soft-glow', 128, 128);
            if (canvas) {
                const ctx = canvas.getContext();
                const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
                grad.addColorStop(0, 'rgba(243, 242, 238, 0.6)');
                grad.addColorStop(0.4, 'rgba(252, 248, 239, 0.4)');
                grad.addColorStop(1, 'rgba(255, 255, 255, 0)');    
                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, 128, 128);
                canvas.refresh();
            }
        }
    }
    createEventsForScene() {
        const onWorldEnter = (world: WorldInfo) => {
            this.activeWorld = world;
            this.activeWorldFightScene = regionsHighlight.filter(region => region.id === this.activeWorld.id)[0].scene;
            this.worldTweens.forEach((worldTween, idx) => {
                const waypoint = worldTween.waypoint;
                const region = worldTween.regionHighLight;
                if (idx != this.activeWorld.id) {
                    const target = waypoint.targets[0] as Phaser.GameObjects.Image;
                    waypoint.pause();
                    target.setVisible(false);
                    region.setVisible(false);
                    
                    this.enterWorldBtn.setVisible(false);
                    
                    this.leaveWorldBtn.setPosition(
                        this.activeHero.x - this.leaveWorldBtn.width / 2 - 15,
                        this.activeHero.y + 150
                    );
                    this.moveInWorldBtn.setPosition(
                        this.activeHero.x + this.moveInWorldBtn.width / 2 + 15,
                        this.activeHero.y + 150
                    );
                    this.leaveWorldBtn.setVisible(true);
                    this.moveInWorldBtn.setVisible(true);
                }
            });
        };
        EventBus.on(GAME_EVENTS.ENTER_WORLD, onWorldEnter);

        const onWorldLeave = () => {
            this.worldTweens.forEach((worldTween, idx) => {
                const waypoint = worldTween.waypoint;
                const region = worldTween.regionHighLight;
                if (idx !== this.activeWorld.id){
                    const target = waypoint.targets[0] as Phaser.GameObjects.Image;
                    target.setVisible(true);
                    waypoint.restart();
                    region.setVisible(true);
                } else {
                    worldTween.waypoint.restart();
                }
            });
            
            this.activeWorld = null;
            this.input.keyboard?.emit('keydown-ESC');
            this.leaveWorldBtn.setVisible(false);
            this.moveInWorldBtn.setVisible(false);
        };
        EventBus.on(GAME_EVENTS.LEAVE_WORLD, onWorldLeave);

        const onFightActive = (data: WebSocketFightMessage["data"]) => {
            this.scene.sleep();
            this.scene.launch('FightScene', {
                creatureName: data.creatureName,
                creatureLevel: data.creatureLevel,
                creatureLife: data.creatureLife,
                creatureMaxLife: data.creatureMaxLife,
                scenarioName: this.activeWorldFightScene
            });
        };
        EventBus.on(GAME_EVENTS.FIGHT, onFightActive);

        const cleanUp = () => {
            EventBus.off(GAME_EVENTS.ENTER_WORLD, onWorldEnter);
            EventBus.off(GAME_EVENTS.LEAVE_WORLD, onWorldLeave);
            EventBus.off(GAME_EVENTS.FIGHT, onFightActive);
        };
        this.events.once(Phaser.Scenes.Events.SHUTDOWN, cleanUp);
        this.events.once(Phaser.Scenes.Events.DESTROY, cleanUp);
    }
    createButtons() {
        this.enterWorldBtn = new ImageButton(
            this,
            this.cameras.main.centerX, 
            this.cameras.main.centerY + 200, 
            'btn-world-ui',
            'btn-world-ui-disabled',
            'Enter World',
            {
                width: 300,
                height: 75,
                textStyle: {
                    fontFamily: 'Georgia',
                    fontSize: '24px'
                }
            }
        ).setVisible(false).setDepth(2);
        this.leaveWorldBtn = new ImageButton(
            this,
            this.cameras.main.centerX,
            this.cameras.main.centerY + 200,
            'btn-world-ui',
            'btn-world-ui-disabled',
            'Leave World',
            {
                width: 200,
                height: 50,
                textStyle: {
                    fontFamily: 'Georgia',
                    fontSize: '14px'
                }
            }
        ).setVisible(false).setDepth(2);
        this.moveInWorldBtn = new ImageButton(
            this,
            this.cameras.main.centerX,
            this.cameras.main.centerY + 200,
            'btn-world-ui',
            'btn-world-ui-disabled',
            'Move and Fight',
            {
                width: 200,
                height: 50,
                textStyle: {
                    fontFamily: 'Georgia',
                    fontSize: '14px'
                }
            }
        ).setVisible(false).setDepth(2);
    }
    createPlayer(x: number, y: number){
        if(this.activeHero)
            this.activeHero.destroy();
        
        this.activeHero = this.add.sprite(x, y, 'player-sprite').setDisplaySize(150, 150);
        this.activeHero.anims.createFromAseprite('player-sprite');
    }
    create() {
        const gameServices = this.registry.get('services') as GameServices;

        const getPlayerLevel = () => usePlayerStore.getState().player?.playerLevel || 0;
        const setPlayerWorld = (worldId: number) => {
            gameServices.playerService.enterWorld(worldId);
        };

        //Events World
        this.createEventsForScene();

        //Camera setBounds
        this.cameras.main.setZoom(0.8);

        //Create Components
        this.createButtons();

        //Buttons events
        this.enterWorldBtn.setOnClick(()=>{
            setPlayerWorld(this.selectedWorldId);
        });
        this.leaveWorldBtn.setOnClick(()=>{
            gameServices.playerService.leaveWorld();
        });
        this.moveInWorldBtn.setOnClick(()=>{
            if (!this.textures.exists(this.selectedWorldScene)){
                console.error(`[fight-duel]: scene ${this.selectedWorldScene} does not exists.`);
                return;
            }
            this.activeHero.play("Walk");
            gameServices.playerService.moveInWorld();
        });

        //World Selection
        const bg = this.add.image(0, 0, 'world-map').setOrigin(0, 0);
        bg.setDisplaySize(1280, 720);

        //Textures
        this.createTextures();

        // World map highlight regions
        regionsHighlight.forEach((region)=>{
            let world = useWorldStore.getState().getWorldId(region.id);
            const regionHighlight = this.add
                .circle(region.x, region.y, region.radius, 0xcccc00)
                .setAlpha(0.01)
                .setInteractive({ useHandCursor: true});
                
            const pointLight = this.add.image(region.x, region.y, 'soft-glow')
                .setDisplaySize(region.radius * 2.8, region.radius * 2.8)
                .setBlendMode(Phaser.BlendModes.ADD)
                .setAlpha(0.01);
            const worldWaypoint = this.add.image(region.x, region.y, 'world-waypoint');

            const offsetY = region.y + 60 > this.scale.height ? -60 : 50;
            const worldCard = this.add.container(region.x, region.y).setDepth(1);
            const background = this.add.image(0, 0, 'world-selector').setDisplaySize(
                150, 85
            ).setAlpha(0.9);

            const worldDescription = this.add.text(
                0, 0, 
                `${world?.worldName}\nLevel: ${world.worldMinLevel}-${world.worldMaxLevel}`, 
                { 
                    fontSize: '14px',
                    align: 'center'
                }
            ).setOrigin(0.5);

            worldCard.add([background, worldDescription]);
            worldCard.setAlpha(0.01);

            //World Effects
            this.worldTweens.set(world.id, {
                waypoint: this.tweens.add({
                    targets: worldWaypoint,
                    y: '-=15',
                    duration: 1000,
                    ease: 'Sine.easeInOut',
                    yoyo: true,
                    repeat: -1,
                    angle: 60
                }),
                regionHighLight: regionHighlight
            });

            regionHighlight.on('pointerover', () => {
                this.tweens.killTweensOf([pointLight, worldCard]);

                this.tweens.add({
                    targets: pointLight,
                    alpha: 1.0,
                    duration: 200,
                    ease: 'Cubic.easeOut'
                });
                this.tweens.add({
                    targets: worldCard,
                    alpha: 1.0,
                    y: region.y + offsetY,
                    duration: 150,
                    ease: 'Cubic.easeOut'
                });
            });
            regionHighlight.on('pointerout', () => {
                this.tweens.add({
                    targets: pointLight,
                    alpha: 0.01,
                    duration: 250,
                    ease: 'Cubic.easeOut'
                })
                this.tweens.add({
                    targets: worldCard,
                    alpha: 0.01,
                    delay: 150,
                    y: region.y,
                    duration: 250,
                    ease: 'Cubic.easeOut'
                });
            });
            regionHighlight.on('pointerdown', ()=>{
                this.selectedWorldId = world.id;
                this.selectedWorldScene = region.scene;
                if (this.activeWorldWaypoint == regionHighlight) return;

                if (this.input.keyboard)
                    this.input.keyboard.enabled = false;

                this.activeWorldWaypoint = regionHighlight;
                this.createPlayer(region.x, region.y-150);
                this.tweens.add({
                    targets: this.activeHero,
                    y: region.y,
                    duration: 200,
                    ease: 'Bounce.easeOut',
                    onComplete: ()=>{
                        if (this.input.keyboard)
                            this.input.keyboard.enabled = true;
                        
                        if(!this.activeHero) return;
                        this.activeHero.play({ key: 'Idle', repeat: -1 });
                        this.cameras.main.pan(region.x, region.y, 200, 'Cubic.easeOut');
                        this.cameras.main.zoomTo(1.2, 200, 'Cubic.easeOut');

                        this.enterWorldBtn.setPosition(
                            region.x,
                            region.y + 180
                        );

                        if (getPlayerLevel() > world.worldMaxLevel || getPlayerLevel() < world.worldMinLevel) {
                            this.enterWorldBtn.setVisible(true).setDisabled();
                        } else {
                            this.enterWorldBtn.setVisible(true).setEnabled();
                        }
                    }
                });
            });

            if (this.activeWorld?.id === world.id){
                regionHighlight.emit('pointerdown');
            }
        });

        // Keyboard events
        this.input.keyboard?.once('keydown-SPACE', ()=>{
            this.scene.start('FightScene',{
                creatureName: 'Vagabonds',
                creatureLevel: 12,
                scenarioName: 'act1-world-scene'
            });
        });
        this.input.keyboard?.on('keydown-ESC', ()=>{
            this.tweens.add({
                targets: this.activeHero,
                y: this.activeHero.y-200,
                duration: 250,
                ease: 'Quadratic.easeOut',
                onComplete: ()=>{
                    if(!this.activeHero) return;
                    this.activeHero?.destroy();
                    this.activeWorldWaypoint = undefined;
                }
            });
            this.cameras.main.zoomTo(0.8, 500, 'Cubic.easeOut', true);
            this.cameras.main.pan(this.cameras.main.centerX, this.cameras.main.centerY, 500, 'Cubic.easeOut', true);
            this.enterWorldBtn.setVisible(false);
        });
    }
    update() {            
    }
}