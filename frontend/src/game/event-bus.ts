import Phaser from 'phaser';

export const GAME_EVENTS = {
    // World Events
    ENTER_WORLD: 'player:enter_world',
    LEAVE_WORLD: 'player:leave_world',

    //Recover
    PLAYER_RECOVER_STATUS: 'player:recover.status',
    
    //Player
    UPDATE_PLAYER: 'player:update',

    // Fight Events
    FIGHT: 'player:fight',
    FIGHT_UPDATE: 'player:fight_update',
    FIGHT_DROP_ITEMS: 'player:fight_drop_items',
    FIGHT_FINISH: 'player:fight_finish'
} as const;

export const EventBus = new Phaser.Events.EventEmitter();