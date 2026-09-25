// RECEIVE MESSAGES
export interface WebSocketMessage {
    action: string;
    data: unknown;
};

export interface WebSocketFightMessage extends WebSocketMessage {
    action: "fight";
    data: {
        fightId: number;
        creatureName: string;
        creatureLevel: number;
        creatureLife: number;
        creatureMaxLife: number;
    }
};

export interface WebSocketFightUpdate extends WebSocketMessage {
    action: "fight.update";
    data: {
        isPlayerAlive: boolean;
        isMonsterAlive: boolean;
        isFightOver: boolean;
        isPlayerAttacking: number;
        isCreatureAttacking: number;
        playerLife: number;
        playerStamina: number;
        playerAttackDamage: number;
        creatureLife: number;
        creatureLevel: number;
        creatureAttackDamage: number;
    }
};

export interface WebSocketFightDropItems extends WebSocketMessage {
    action: "fight.drop.items";
    data: {
        id: number;
        itemName: string;
        itemPower: number;
        itemWeight: number;
        itemType: string;
        itemConsumableType: string | null;
    }[];
};

export interface WebSocketFightFinish extends WebSocketMessage {
    action: "fight.finish";
    data: {
        isPlayerAlive: boolean;
        isMonsterAlive: boolean;
        isFightOver: boolean;
        isPlayerAttacking: number;
        isCreatureAttacking: number;
        playerLife: number;
        playerStamina: number;
        creatureLife: number;
        creatureLevel: number;
    }
};

export type FightMessage = 
    | WebSocketFightMessage 
    | WebSocketFightUpdate 
    | WebSocketFightDropItems 
    | WebSocketFightFinish;

export interface WebSocketWorldEnterMessage extends WebSocketMessage {
    action: "world.enter";
    data: {
        id: number;
        worldName: string;
        worldMinLevel: number;
        worldMaxLevel: number;
    }
};

export interface WebSocketWorldLeaveMessage extends WebSocketMessage {
    action: "world.leave";
};

export type WorldMessage = WebSocketWorldEnterMessage | WebSocketWorldLeaveMessage;

export interface WebSocketRecoverStatusMessage extends WebSocketMessage {
    action: "player.recover.status";
    data: {
        playerLife: number;
        playerStamina: number;
    }
};

export type RecoverStatusMessage = WebSocketRecoverStatusMessage;

export interface WebSocketInventoryUpdateMessage extends WebSocketMessage {
    action: "inventory.update";
    data: {
        id: number;
        itemName: string;
        itemPower: number;
        itemWeight: number;
        itemType: string;
        itemConsumableType: string | null;
    }[]
};

export type InventoryMessage = WebSocketInventoryUpdateMessage;

export type AnyMessage = 
    | RecoverStatusMessage
    | FightMessage 
    | WorldMessage 
    | InventoryMessage;

// SEND MESSAGES
export interface WebSocketSendMessage {
    action: string;
    data?: unknown;
};

export interface WebSocketSendAttackMessage extends WebSocketSendMessage {
    action: "attack";
};

export interface WebSocketSendFleeMessage extends WebSocketSendMessage {
    action: "flee";
};

export interface WebSocketSendEnterWorldMessage extends WebSocketSendMessage {
    action: "enter.world";
    data: number;
};

export interface WebSocketSendLeaveWorldMessage extends WebSocketSendMessage {
    action: "leave.world";
};

export interface WebSocketSendMoveInWorldMessage extends WebSocketSendMessage {
    action: "move";
};

export interface WebSocketSendLootItemsMessage extends WebSocketSendMessage {
    action: "loot";
    data: number[];
};

export interface WebSocketGetInventoryMessage extends WebSocketSendMessage {
    action: "get.inventory";
};

export interface WebSocketUseItemMessage extends WebSocketSendMessage {
    action: "use";
    data: number;
};

export interface WebSocketSalvageItemMessage extends WebSocketSendMessage {
    action: "salvage";
    data: number;
};

export type SendMessage = 
    | WebSocketSendAttackMessage 
    | WebSocketSendFleeMessage
    | WebSocketSendEnterWorldMessage
    | WebSocketSendLeaveWorldMessage
    | WebSocketSendMoveInWorldMessage
    | WebSocketSendLootItemsMessage
    | WebSocketGetInventoryMessage
    | WebSocketUseItemMessage
    | WebSocketSalvageItemMessage;
